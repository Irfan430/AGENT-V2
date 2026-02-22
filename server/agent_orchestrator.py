"""
Production-grade agent orchestrator implementing the agentic loop.
Manages the Thought-Action-Observation-Reflection workflow with real tool execution.
Fixed: infinite loop bug, tool result handling, conversation memory integration.
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
from server.error_handler import (
    ErrorHandler, SelfCorrectionEngine, ErrorType, RecoveryStrategy,
    get_error_handler, get_self_correction_engine
)
from server.memory_manager import get_memory_manager

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Orchestrates the agent's agentic loop with real tool execution.
    Implements Thought-Action-Observation-Reflection cycle.
    Fixed: proper termination after tool success, conversation context accumulation.
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
            state.context.update(context)
        
        # Accumulate tool results for final response generation
        tool_results_summary = []
        
        logger.info(f"Starting production agent loop for conversation {conversation_id}")
        
        # Store user message in memory (handled at end with full exchange)
        
        # Main agentic loop
        while state.iteration < state.max_iterations:
            try:
                # Increment iteration
                state = increment_iteration(state)
                logger.info(f"Iteration {state.iteration}/{state.max_iterations}")
                
                # Phase 1: Thought - Agent thinks about the task
                state = await self._thought_phase(state, tool_results_summary)
                
                # Check if we should stop (agent decided to respond)
                if state.thought and state.thought.next_action.lower() in ["respond", "final_answer", "done"]:
                    logger.info("Agent decided to respond - generating final answer")
                    state = await self._generate_final_response(state, tool_results_summary)
                    break
                
                # Phase 2: Action - Agent takes action (Tool Call)
                state = await self._action_phase(state)
                
                # Phase 3: Observation - Execute tool and observe results
                state = await self._observation_phase(state)
                
                # Accumulate tool results
                if state.observations:
                    last_obs = state.observations[-1]
                    if last_obs.success:
                        tool_name = state.thought.next_action if state.thought else "unknown"
                        tool_results_summary.append({
                            "tool": tool_name,
                            "result": last_obs.result,
                            "iteration": state.iteration
                        })
                
                # Phase 4: Reflection - Reflect on the results if errors occur
                if state.observations and not state.observations[-1].success and self.config.enable_reflection:
                    state = await self._reflection_phase(state)
                
                # Check termination conditions
                if self._should_terminate(state):
                    logger.info("Termination condition met")
                    # Generate final response if we have tool results but no response yet
                    if not state.response and tool_results_summary:
                        state = await self._generate_final_response(state, tool_results_summary)
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
                    state.response = f"I encountered an error while processing your request: {str(e)}"
                    state.success = False
                    break
        
        # If no response generated, create a fallback
        if not state.response:
            if tool_results_summary:
                state = await self._generate_final_response(state, tool_results_summary)
            else:
                state.response = "I was unable to complete the task. Please try again."
                state.success = False
        
        # Store conversation exchange in memory
        try:
            if state.response:
                self.memory_manager.store_conversation(
                    conversation_id=conversation_id,
                    user_message=user_message,
                    agent_response=state.response
                )
        except Exception as e:
            logger.warning(f"Failed to store conversation in memory: {e}")
        
        # Finalize state
        state.updated_at = datetime.now()
        logger.info(f"Agent loop completed for conversation {conversation_id}")
        
        return state
    
    async def _thought_phase(self, state: AgentState, tool_results: List[Dict] = None) -> AgentState:
        """
        Thought phase: Agent analyzes the task and plans approach.
        """
        logger.info("=== THOUGHT PHASE ===")
        
        try:
            available_tools = self.tool_manager.get_tools_list()
            
            # Build conversation context
            conversation_history = []
            try:
                conversation_history = self.memory_manager.get_conversation_history(state.conversation_id)
            except Exception:
                pass
            
            history_str = ""
            if conversation_history:
                history_str = "\n".join([
                    f"{msg.get('metadata', {}).get('role', 'unknown')}: {msg.get('text', '')}"
                    for msg in conversation_history[-10:]  # Last 10 messages
                ])
            
            # Build tool results context
            tool_results_str = ""
            if tool_results:
                tool_results_str = "\n\nPrevious tool results:\n" + "\n".join([
                    f"- {r['tool']}: {str(r['result'])[:500]}"
                    for r in tool_results
                ])
            
            # Build previous actions context
            prev_actions_str = ""
            if state.actions:
                prev_actions_str = "\n\nPrevious actions taken:\n" + "\n".join([
                    f"- {a.description}" for a in state.actions[-5:]
                ])
            
            last_correction = state.context.get("last_correction_message", "")

            thinking_prompt = f"""You are an autonomous AI agent. Analyze the task and decide the next step.

Task: {state.user_message}

{f"Conversation History:{chr(10)}{history_str}" if history_str else ""}
{tool_results_str}
{prev_actions_str}
{f"Self-correction note: {last_correction}" if last_correction else ""}

Available Tools:
{json.dumps(available_tools, indent=2)}

IMPORTANT DECISION RULES:
- If you have enough information to answer the user's question, set next_action to "respond"
- If you need to use a tool, specify the exact tool name
- If you just got tool results and can now answer, set next_action to "respond"
- Do NOT repeat the same tool call if it already succeeded
- After 1-2 successful tool calls, you should usually "respond"

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
                    content = content[7:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                elif content.startswith("```"):
                    content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                response_data = json.loads(content)
                thought = Thought(
                    reasoning=response_data.get("reasoning", ""),
                    plan=response_data.get("plan", []),
                    next_action=response_data.get("next_action", "respond"),
                    confidence=float(response_data.get("confidence", 0.5))
                )
                state.context["next_tool_input"] = response_data.get("tool_input", {})
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse JSON thought: {str(e)}. Raw: {response.content[:200]}")
                # If we have tool results, just respond
                next_action = "respond"
                thought = Thought(
                    reasoning=f"Proceeding to respond based on available information.",
                    plan=["Generate final response"],
                    next_action=next_action,
                    confidence=0.7
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
            
            if next_action_name in ["respond", "final_answer", "done"]:
                action = Action(
                    type=ActionType.RESPONSE,
                    description="Generating final response to user"
                )
            else:
                from server.agent_state import ToolCall
                tool_input = state.context.get("next_tool_input", {})
                action = Action(
                    type=ActionType.TOOL_CALL,
                    description=f"Calling tool: {next_action_name}",
                    tool_call=ToolCall(tool_name=next_action_name, tool_input=tool_input)
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
                if tool_call is None:
                    observation = Observation(
                        action_type=ActionType.TOOL_CALL,
                        result="No tool call specified",
                        success=False,
                        error="tool_call is None"
                    )
                    state = update_state_with_observation(state, observation)
                    return state
                # ToolCall is a Pydantic model, use attribute access
                tool_name = tool_call.tool_name if hasattr(tool_call, 'tool_name') else tool_call.get('tool_name', '')
                tool_input = tool_call.tool_input if hasattr(tool_call, 'tool_input') else tool_call.get('tool_input', {})
                result = await self.tool_manager.execute_tool(tool_name, tool_input)
                observation = Observation(
                    action_type=ActionType.TOOL_CALL,
                    result=json.dumps(result),
                    success=result.get("success", False),
                    error=result.get("error")
                )
            elif last_action.type == ActionType.RESPONSE:
                # Will be handled by _generate_final_response
                observation = Observation(
                    action_type=ActionType.RESPONSE,
                    result="Preparing final response",
                    success=True
                )
            else:
                observation = Observation(
                    action_type=last_action.type,
                    result="No operation",
                    success=True
                )
            
            state = update_state_with_observation(state, observation)
            return state
        
        except Exception as e:
            logger.error(f"Error in observation phase: {str(e)}")
            raise

    async def _generate_final_response(
        self,
        state: AgentState,
        tool_results: List[Dict] = None
    ) -> AgentState:
        """
        Generate the final response to the user based on accumulated context.
        """
        logger.info("=== GENERATING FINAL RESPONSE ===")
        
        try:
            # Build context from tool results
            context_parts = [f"User request: {state.user_message}"]
            
            if tool_results:
                context_parts.append("\nInformation gathered:")
                for r in tool_results:
                    try:
                        result_data = json.loads(r['result']) if isinstance(r['result'], str) else r['result']
                        if isinstance(result_data, dict) and result_data.get('result'):
                            inner = result_data['result']
                            if isinstance(inner, dict) and inner.get('items'):
                                # Directory listing
                                items = inner['items']
                                item_names = [item['name'] for item in items[:20]]
                                context_parts.append(f"- {r['tool']} result: {item_names}")
                            elif isinstance(inner, str):
                                context_parts.append(f"- {r['tool']} result: {inner[:500]}")
                            else:
                                context_parts.append(f"- {r['tool']} result: {str(inner)[:500]}")
                        else:
                            context_parts.append(f"- {r['tool']} result: {str(result_data)[:500]}")
                    except Exception:
                        context_parts.append(f"- {r['tool']} result: {str(r['result'])[:300]}")
            
            response_prompt = "\n".join(context_parts) + "\n\nBased on the above information, provide a clear and helpful response to the user's request."
            
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
            state.success = True
            
            # Add final observation
            observation = Observation(
                action_type=ActionType.RESPONSE,
                result=state.response,
                success=True
            )
            state = update_state_with_observation(state, observation)
            
            return state
            
        except Exception as e:
            logger.error(f"Error generating final response: {str(e)}")
            state.response = f"I encountered an error generating the response: {str(e)}"
            state.success = False
            return state

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
                error=Exception(last_observation.error or "Unknown error"),
                context=error_context,
                llm_client=self.llm_manager,
                system_prompt=get_system_prompt(),
                available_tools=self.tool_manager.get_tools_list()
            )
            
            if correction_attempted and correction_message:
                logger.info(f"Self-correction attempted: {correction_message}")
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
                state.error_count = 0
                state.context["last_correction_message"] = correction_message
            else:
                logger.warning("Self-correction failed. Using basic reflection.")
                reflection_prompt = f"An error occurred. Analyze and suggest a new plan.\nError: {last_observation.error}"
                messages = [Message(role="user", content=reflection_prompt)]
                response = await self.llm_manager.chat_completion_async(messages=messages)
                
                reflection = Reflection(
                    observation=last_observation.result,
                    analysis=response.content,
                    lessons_learned=["Error encountered, adjusting approach"],
                    adjustments=["Try alternative approach"]
                )
                state = update_state_with_reflection(state, reflection)
            
            return state
        
        except Exception as e:
            logger.error(f"Error in reflection phase: {str(e)}")
            raise

    def _should_terminate(self, state: AgentState) -> bool:
        """
        Check if the agent loop should terminate.
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
