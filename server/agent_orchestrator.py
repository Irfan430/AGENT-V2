"""
Production-grade agent orchestrator implementing the agentic loop.
Manages the Thought-Action-Observation-Reflection workflow with real tool execution.
Implements Phase 3.1, 3.2 and 4 of the Production Roadmap.
"""

import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime

from server.agent_state import (
    AgentState, Thought, Action, Observation, Reflection,
    ActionType, create_initial_state, update_state_with_thought,
    update_state_with_action, update_state_with_observation,
    update_state_with_reflection, increment_iteration
)
from server.llm_client import get_llm_client, Message
from server.agent_config import get_system_prompt, AgentStateConfig
from server.tool_manager import get_tool_manager
from server.error_handler import ErrorHandler, SelfCorrectionEngine, ErrorType, RecoveryStrategy, get_error_handler, get_self_correction_engine
from server.memory_manager import get_memory_manager

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Orchestrates the agent's agentic loop with real tool execution.
    Implements Thought-Action-Observation-Reflection cycle.
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.llm_manager = get_llm_client()
        self.tool_manager = get_tool_manager()
        self.memory_manager = get_memory_manager()
        self.error_handler = get_error_handler()
        self.self_correction_engine = get_self_correction_engine()
        self.config = AgentStateConfig()
        logger.info("Production Agent orchestrator initialized with self-correction")
    
    async def run_agent_loop(
        self,
        conversation_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Run the complete agentic loop for a user message.
        """
        # Create initial state
        state = create_initial_state(conversation_id, user_message)
        if context:
            state.context = context
        
        logger.info(f"Starting production agent loop for conversation {conversation_id}")
        
        # Main agentic loop
        while state.iteration < state.max_iterations:
            try:
                # Increment iteration
                state = increment_iteration(state)
                logger.info(f"Iteration {state.iteration}/{state.max_iterations}")
                
                # Phase 1: Thought - Agent thinks about the task
                state = await self._thought_phase(state)
                
                # Check if we should stop (agent decided to respond)
                if state.thought and state.thought.next_action.lower() == "respond":
                    logger.info("Agent decided to respond")
                    state = await self._action_phase(state)
                    state = await self._observation_phase(state)
                    break
                
                # Phase 2: Action - Agent takes action (Tool Call)
                state = await self._action_phase(state)
                
                # Phase 3: Observation - Execute tool and observe results
                state = await self._observation_phase(state)
                
                # Phase 4: Reflection - Reflect on the results if errors occur
                if not state.observations[-1].success and self.config.enable_reflection:
                    state = await self._reflection_phase(state)
                
                # Check termination conditions
                if self._should_terminate(state):
                    logger.info("Termination condition met")
                    break
            
            except Exception as e:
                logger.error(f"Critical error in agent loop iteration {state.iteration}: {str(e)}")
                state.errors.append({
                    "iteration": state.iteration,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                state.error_count += 1
                
                if state.error_count >= self.config.max_consecutive_errors:
                    state.response = f"Agent encountered too many critical errors: {str(e)}"
                    state.success = False
                    break
        
        # Finalize state
        state.updated_at = datetime.now()
        logger.info(f"Agent loop completed for conversation {conversation_id}")
        
        return state
    
    async def _thought_phase(self, state: AgentState) -> AgentState:
        """
        Thought phase: Agent analyzes the task and plans approach.
        """
        logger.info("=== THOUGHT PHASE ===")
        
        try:
            available_tools = self.tool_manager.get_tools_list()
            conversation_history = self.memory_manager.get_conversation_history(state.conversation_id)
            
            history_str = "\n".join([f"{msg['metadata'].get('role', 'unknown')}: {msg['text']}" for msg in conversation_history])

            thinking_prompt = f"""Analyze the task and decide the next step.

Task: {state.user_message}
Conversation History:
{history_str}

Available Tools:
{json.dumps(available_tools, indent=2)}

{state.context.get("last_correction_message", "")}

Please provide your response in JSON format:
{{
  "reasoning": "Your detailed reasoning about the current state and next step",
  "plan": ["Step 1", "Step 2", ...],
  "next_action": "The name of the tool to call, or 'respond' to give the final answer",
  "tool_input": {{ "param1": "value1", ... }},
  "confidence": 0.9
}}
"""
            
            messages = [
                Message(role="system", content=get_system_prompt()),
                Message(role="user", content=thinking_prompt)
            ]
            
            response = await self.llm_manager.chat_completion_async(
                messages=messages,
                temperature=0.2,
                max_tokens=1024
            )
            
            try:
                content = response.content.strip()
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                    
                response_data = json.loads(content)
                thought = Thought(
                    reasoning=response_data.get("reasoning", ""),
                    plan=response_data.get("plan", []),
                    next_action=response_data.get("next_action", "respond"),
                    confidence=float(response_data.get("confidence", 0.5))
                )
                state.context["next_tool_input"] = response_data.get("tool_input", {})
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON thought: {str(e)}. Raw: {response.content}")
                thought = Thought(
                    reasoning=f"Error parsing thought: {str(e)}. Raw response: {response.content}",
                    plan=["Attempt to recover from parsing error"],
                    next_action="respond",
                    confidence=0.1
                )
            
            state = update_state_with_thought(state, thought)
            return state
        
        except Exception as e:
            logger.error(f"Error in thought phase: {str(e)}")
            raise
    
    async def _action_phase(self, state: AgentState) -> AgentState:
        """
        Action phase: Agent prepares the planned action.
        """
        logger.info("=== ACTION PHASE ===")
        
        try:
            if not state.thought:
                return state
            
            next_action_name = state.thought.next_action.lower()
            
            if next_action_name == "respond":
                action = Action(
                    type=ActionType.RESPONSE,
                    description="Generating final response to user"
                )
            else:
                tool_input = state.context.get("next_tool_input", {})
                action = Action(
                    type=ActionType.TOOL_CALL,
                    description=f"Calling tool: {next_action_name}",
                    tool_call={"tool_name": next_action_name, "tool_input": tool_input}
                )
            
            state = update_state_with_action(state, action)
            return state
        
        except Exception as e:
            logger.error(f"Error in action phase: {str(e)}")
            raise

    async def _observation_phase(self, state: AgentState) -> AgentState:
        """
        Observation phase: Execute the action and observe the result.
        """
        logger.info("=== OBSERVATION PHASE ===")
        
        try:
            last_action = state.actions[-1]
            
            if last_action.type == ActionType.TOOL_CALL:
                tool_call = last_action.tool_call
                result = await self.tool_manager.execute_tool(tool_call['tool_name'], tool_call['tool_input'])
                observation = Observation(
                    action_type=ActionType.TOOL_CALL,
                    result=json.dumps(result),
                    success=result.get("success", False),
                    error=result.get("error")
                )
            elif last_action.type == ActionType.RESPONSE:
                # Generate final response using LLM
                response_prompt = f"Based on the conversation so far, provide a final response to the user's request: {state.user_message}"
                messages = [Message(role="user", content=response_prompt)]
                response = await self.llm_manager.chat_completion_async(messages=messages)
                state.response = response.content
                state.success = True
                observation = Observation(action_type=ActionType.RESPONSE, result=state.response, success=True)
            else:
                observation = Observation(action_type=last_action.type, result="No operation", success=True)
            
            state = update_state_with_observation(state, observation)
            return state
        
        except Exception as e:
            logger.error(f"Error in observation phase: {str(e)}")
            raise

    async def _reflection_phase(self, state: AgentState) -> AgentState:
        """
        Reflection phase: Agent reflects on errors and adjusts the plan.
        """
        logger.info("=== REFLECTION PHASE ===")
        
        try:
            last_observation = state.observations[-1]
            error_context = {
                "user_message": state.user_message,
                "last_action": state.actions[-1].dict() if state.actions else None,
                "last_observation": last_observation.dict()
            }
            
            correction_attempted, correction_message = await self.self_correction_engine.attempt_correction(
                error=Exception(last_observation.error),
                context=error_context,
                llm_client=self.llm_manager,
                system_prompt=get_system_prompt(),
                available_tools=self.tool_manager.get_tools_list()
            )
            
            if correction_attempted and correction_message:
                logger.info(f"Self-correction attempted: {correction_message}")
                # If self-correction suggests a new thought/plan, update the state
                if "new_thought_from_reflection" in error_context:
                    new_thought_data = error_context["new_thought_from_reflection"]
                    new_thought = Thought(
                        reasoning=new_thought_data.get("reasoning", ""),
                        plan=new_thought_data.get("plan", []),
                        next_action=new_thought_data.get("next_action", "respond"),
                        confidence=float(new_thought_data.get("confidence", 0.5))
                    )
                    state = update_state_with_thought(state, new_thought)
                    state.context["next_tool_input"] = new_thought_data.get("tool_input", {})
                state.error_count = 0 # Reset error count after successful correction attempt
                state.context["last_correction_message"] = correction_message
            else:
                logger.warning("Self-correction failed or not applicable. Falling back to basic reflection.")
                reflection_prompt = f"An error occurred. Analyze the error and suggest a new plan.\nError: {last_observation.error}"
                
                messages = [Message(role="user", content=reflection_prompt)]
                response = await self.llm_manager.chat_completion_async(messages=messages)
                
                reflection = Reflection(
                    observation=last_observation.result,
                    analysis=response.content,
                    lessons_learned=["Lesson 1"],
                    adjustments=["Adjustment 1"]
                )
                
                state = update_state_with_reflection(state, reflection)
            return state
        
        except Exception as e:
            logger.error(f"Error in reflection phase: {str(e)}")
            raise

    def _should_terminate(self, state: AgentState) -> bool:
        """
        Check if the agent loop should terminate.
        Termination conditions: success, max iterations reached, or too many consecutive errors.
        """
        if state.success:
            return True
        if state.iteration >= state.max_iterations:
            return True
        if state.error_count >= self.config.max_consecutive_errors:
            return True
        return False

# Global instance
_orchestrator = None

def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
