"""
Production-grade agent orchestrator implementing the agentic loop.
Manages the Thought-Action-Observation-Reflection workflow with real tool execution.
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
        self.config = AgentStateConfig()
        logger.info("Production Agent orchestrator initialized")
    
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
                if self.config.enable_reflection and state.error_count >= self.config.reflection_threshold:
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
                
                if state.error_count >= 5: # Increased tolerance for production
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
            # Prepare context for thinking
            available_tools = self.tool_manager.get_tools_list()
            
            history_context = ""
            if state.actions and state.observations:
                history_context = "\nPrevious Actions and Observations:\n"
                for i in range(len(state.actions)):
                    action = state.actions[i]
                    obs = state.observations[i] if i < len(state.observations) else None
                    history_context += f"Action {i+1}: {action.type} - {action.description}\n"
                    if obs:
                        history_context += f"Observation {i+1}: {'Success' if obs.success else 'Failure'} - {obs.result[:500]}...\n"

            thinking_prompt = f"""Analyze the task and decide the next step.

Task: {state.user_message}
Current Iteration: {state.iteration}/{state.max_iterations}
{history_context}

Available Tools:
{json.dumps(available_tools, indent=2)}

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
                temperature=0.2, # Lower temperature for more consistent JSON
                max_tokens=1024
            )
            
            # Parse response
            try:
                # Clean response content if it contains markdown code blocks
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
                # Store tool input in context for action phase
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
                # It's a tool call
                tool_input = state.context.get("next_tool_input", {})
                action = Action(
                    type=ActionType.TOOL_CALL,
                    description=f"Calling tool: {next_action_name}",
                    input=tool_input
                )
            
            state = update_state_with_action(state, action)
            return state
        
        except Exception as e:
            logger.error(f"Error in action phase: {str(e)}")
            raise
    
    async def _observation_phase(self, state: AgentState) -> AgentState:
        """
        Observation phase: Execute the action and observe results.
        """
        logger.info("=== OBSERVATION PHASE ===")
        
        try:
            if not state.actions:
                return state
            
            last_action = state.actions[-1]
            
            if last_action.type == ActionType.RESPONSE:
                # Generate final response using LLM
                response_prompt = f"""Based on the task and all previous observations, provide the final response to the user.

Task: {state.user_message}

History:
{json.dumps(state.context.get('history', []), indent=2)}

Provide a clear, comprehensive, and helpful response."""
                
                messages = [
                    Message(role="system", content=get_system_prompt()),
                    Message(role="user", content=response_prompt)
                ]
                
                response = await self.llm_manager.chat_completion_async(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048
                )
                
                state.response = response.content
                observation = Observation(
                    action_type=ActionType.RESPONSE,
                    result="Final response generated",
                    success=True
                )
            
            elif last_action.type == ActionType.TOOL_CALL:
                # Execute the actual tool
                tool_name = state.thought.next_action
                tool_input = last_action.input or {}
                
                tool_result = await self.tool_manager.execute_tool(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    user_approved=True # Auto-approve for now in this loop
                )
                
                if tool_result["success"]:
                    observation = Observation(
                        action_type=ActionType.TOOL_CALL,
                        result=str(tool_result["result"]),
                        success=True
                    )
                else:
                    observation = Observation(
                        action_type=ActionType.TOOL_CALL,
                        result="",
                        success=False,
                        error=tool_result["error"]
                    )
                    state.error_count += 1
            
            else:
                observation = Observation(
                    action_type=ActionType.PLANNING,
                    result="Planning step completed",
                    success=True
                )
            
            state = update_state_with_observation(state, observation)
            return state
        
        except Exception as e:
            logger.error(f"Error in observation phase: {str(e)}")
            observation = Observation(
                action_type=ActionType.TOOL_CALL,
                result="",
                success=False,
                error=str(e)
            )
            state = update_state_with_observation(state, observation)
            state.error_count += 1
            return state
    
    async def _reflection_phase(self, state: AgentState) -> AgentState:
        """
        Reflection phase: Agent reflects on errors and adjusts approach.
        """
        logger.info("=== REFLECTION PHASE ===")
        
        try:
            reflection_prompt = f"""You have encountered errors in your task. Reflect on what went wrong and how to fix it.

Task: {state.user_message}
Errors: {json.dumps(state.errors[-3:], indent=2)}

Provide a reflection on the situation and a new strategy."""
            
            messages = [
                Message(role="system", content=get_system_prompt()),
                Message(role="user", content=reflection_prompt)
            ]
            
            response = await self.llm_manager.chat_completion_async(messages=messages)
            
            reflection = Reflection(
                thought_process=response.content,
                adjustments=["Adjusting strategy based on reflection"],
                confidence_score=0.6
            )
            
            state = update_state_with_reflection(state, reflection)
            return state
        except Exception as e:
            logger.error(f"Error in reflection phase: {str(e)}")
            return state

    def _should_terminate(self, state: AgentState) -> bool:
        """Check if the agent loop should terminate."""
        if state.response:
            return True
        if state.iteration >= state.max_iterations:
            state.response = "Maximum iterations reached without a final answer."
            return True
        return False

# Global orchestrator instance
_orchestrator: Optional[AgentOrchestrator] = None

def get_orchestrator() -> AgentOrchestrator:
    """Get or create the global orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
