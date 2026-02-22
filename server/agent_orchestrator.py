"""
LangGraph-based agent orchestrator implementing the agentic loop.
Manages the Thought-Action-Observation-Reflection workflow.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from agent_state import (
    AgentState, Thought, Action, Observation, Reflection,
    ActionType, create_initial_state, update_state_with_thought,
    update_state_with_action, update_state_with_observation,
    update_state_with_reflection, increment_iteration
)
from llm_client import get_llm_client, Message
from agent_config import get_system_prompt, AgentStateConfig

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Orchestrates the agent's agentic loop using LangGraph-inspired workflow.
    Implements Thought-Action-Observation-Reflection cycle.
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.llm_client = get_llm_client()
        self.config = AgentStateConfig()
        logger.info("Agent orchestrator initialized")
    
    async def run_agent_loop(
        self,
        conversation_id: str,
        user_message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentState:
        """
        Run the complete agentic loop for a user message.
        
        Args:
            conversation_id: ID of the conversation
            user_message: User's message/task
            context: Optional context dictionary
            
        Returns:
            Final agent state with response
        """
        # Create initial state
        state = create_initial_state(conversation_id, user_message)
        if context:
            state.context = context
        
        logger.info(f"Starting agent loop for conversation {conversation_id}")
        
        # Main agentic loop
        while state.iteration < state.max_iterations:
            try:
                # Increment iteration
                state = increment_iteration(state)
                logger.info(f"Iteration {state.iteration}/{state.max_iterations}")
                
                # Phase 1: Thought - Agent thinks about the task
                state = await self._thought_phase(state)
                
                # Check if we should stop
                if state.response:
                    logger.info("Agent decided to respond without further actions")
                    break
                
                # Phase 2: Action - Agent takes action
                state = await self._action_phase(state)
                
                # Phase 3: Observation - Observe the results
                state = await self._observation_phase(state)
                
                # Phase 4: Reflection - Reflect on the results
                if self.config.enable_reflection and state.error_count >= self.config.reflection_threshold:
                    state = await self._reflection_phase(state)
                
                # Check termination conditions
                if self._should_terminate(state):
                    logger.info("Termination condition met")
                    break
            
            except Exception as e:
                logger.error(f"Error in agent loop iteration {state.iteration}: {str(e)}")
                state.errors.append({
                    "iteration": state.iteration,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                state.error_count += 1
                
                if state.error_count >= 3:
                    state.response = f"Agent encountered too many errors: {str(e)}"
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
            # Prepare prompt for thinking
            thinking_prompt = f"""Analyze the following task and create a plan:

Task: {state.user_message}

Context: {json.dumps(state.context, indent=2) if state.context else "None"}

Previous actions: {len(state.actions)}
Previous errors: {state.error_count}

Please provide:
1. Your reasoning about the task
2. A step-by-step plan to solve it
3. The next action you should take
4. Your confidence level (0-1)

Format your response as JSON with keys: reasoning, plan (array), next_action, confidence"""
            
            # Get LLM response
            messages = [
                Message(role="system", content=get_system_prompt()),
                Message(role="user", content=thinking_prompt)
            ]
            
            response = await self.llm_client.chat_completion_async(
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            
            # Parse response
            try:
                response_data = json.loads(response.content)
                thought = Thought(
                    reasoning=response_data.get("reasoning", ""),
                    plan=response_data.get("plan", []),
                    next_action=response_data.get("next_action", ""),
                    confidence=float(response_data.get("confidence", 0.5))
                )
            except json.JSONDecodeError:
                # Fallback if response is not JSON
                thought = Thought(
                    reasoning=response.content,
                    plan=["Execute the task"],
                    next_action="proceed",
                    confidence=0.5
                )
            
            state = update_state_with_thought(state, thought)
            logger.info(f"Thought: {thought.reasoning[:100]}...")
            logger.info(f"Plan: {thought.plan}")
            logger.info(f"Next action: {thought.next_action}")
            
            return state
        
        except Exception as e:
            logger.error(f"Error in thought phase: {str(e)}")
            raise
    
    async def _action_phase(self, state: AgentState) -> AgentState:
        """
        Action phase: Agent executes the planned action.
        """
        logger.info("=== ACTION PHASE ===")
        
        try:
            if not state.thought:
                logger.warning("No thought available for action phase")
                return state
            
            # Determine action type based on thought
            next_action = state.thought.next_action.lower()
            
            if "respond" in next_action or "answer" in next_action:
                # Generate response
                action = Action(
                    type=ActionType.RESPONSE,
                    description="Generate final response"
                )
            elif "tool" in next_action or "execute" in next_action:
                # Tool call action
                action = Action(
                    type=ActionType.TOOL_CALL,
                    description=f"Execute: {next_action}"
                )
            else:
                # Default to planning
                action = Action(
                    type=ActionType.PLANNING,
                    description="Continue planning"
                )
            
            state = update_state_with_action(state, action)
            logger.info(f"Action: {action.type} - {action.description}")
            
            return state
        
        except Exception as e:
            logger.error(f"Error in action phase: {str(e)}")
            raise
    
    async def _observation_phase(self, state: AgentState) -> AgentState:
        """
        Observation phase: Observe the results of the action.
        """
        logger.info("=== OBSERVATION PHASE ===")
        
        try:
            if not state.actions:
                logger.warning("No actions to observe")
                return state
            
            last_action = state.actions[-1]
            
            # Simulate observation based on action type
            if last_action.type == ActionType.RESPONSE:
                # Generate response
                response_prompt = f"""Based on the task and your analysis, provide a comprehensive response:

Task: {state.user_message}
Your reasoning: {state.thought.reasoning if state.thought else "N/A"}
Your plan: {state.thought.plan if state.thought else []}

Provide a clear, helpful response to the user."""
                
                messages = [
                    Message(role="system", content=get_system_prompt()),
                    Message(role="user", content=response_prompt)
                ]
                
                response = await self.llm_client.chat_completion_async(
                    messages=messages,
                    temperature=0.7,
                    max_tokens=2048
                )
                
                state.response = response.content
                
                observation = Observation(
                    action_type=ActionType.RESPONSE,
                    result=response.content[:200] + "...",
                    success=True
                )
            
            elif last_action.type == ActionType.TOOL_CALL:
                # Simulate tool execution
                observation = Observation(
                    action_type=ActionType.TOOL_CALL,
                    result="Tool executed successfully",
                    success=True
                )
            
            else:
                observation = Observation(
                    action_type=ActionType.PLANNING,
                    result="Planning phase completed",
                    success=True
                )
            
            state = update_state_with_observation(state, observation)
            logger.info(f"Observation: {observation.result}")
            
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
            
            return state
    
    async def _reflection_phase(self, state: AgentState) -> AgentState:
        """
        Reflection phase: Agent reflects on errors and adjusts approach.
        """
        logger.info("=== REFLECTION PHASE ===")
        
        try:
            # Prepare reflection prompt
            recent_errors = state.errors[-3:] if state.errors else []
            
            reflection_prompt = f"""Analyze the errors that occurred and suggest improvements:

Task: {state.user_message}
Errors encountered: {json.dumps(recent_errors, indent=2)}
Previous attempts: {state.iteration}

Please provide:
1. Analysis of what went wrong
2. Root cause of the errors
3. Lessons learned
4. Adjustments to the approach

Format your response as JSON with keys: analysis, lessons_learned (array), adjustments (array)"""
            
            messages = [
                Message(role="system", content=get_system_prompt()),
                Message(role="user", content=reflection_prompt)
            ]
            
            response = await self.llm_client.chat_completion_async(
                messages=messages,
                temperature=0.5,
                max_tokens=1024
            )
            
            # Parse reflection
            try:
                response_data = json.loads(response.content)
                reflection = Reflection(
                    observation=f"Analyzed {len(recent_errors)} errors",
                    analysis=response_data.get("analysis", ""),
                    lessons_learned=response_data.get("lessons_learned", []),
                    adjustments=response_data.get("adjustments", [])
                )
            except json.JSONDecodeError:
                reflection = Reflection(
                    observation="Error analysis completed",
                    analysis=response.content,
                    lessons_learned=[],
                    adjustments=[]
                )
            
            state = update_state_with_reflection(state, reflection)
            logger.info(f"Reflection: {reflection.analysis[:100]}...")
            logger.info(f"Adjustments: {reflection.adjustments}")
            
            return state
        
        except Exception as e:
            logger.error(f"Error in reflection phase: {str(e)}")
            return state
    
    def _should_terminate(self, state: AgentState) -> bool:
        """
        Determine if the agent should terminate the loop.
        """
        # Terminate if response is generated
        if state.response:
            return True
        
        # Terminate if max iterations reached
        if state.iteration >= state.max_iterations:
            logger.info(f"Max iterations ({state.max_iterations}) reached")
            return True
        
        # Terminate if too many errors
        if state.error_count >= 5:
            logger.info("Too many errors, terminating")
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
