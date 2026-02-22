"""
Agent state management and data models.
Defines the structure of agent state throughout the agentic loop.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class TaskStatus(str, Enum):
    """Status of a task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class ActionType(str, Enum):
    """Type of action to execute."""
    TOOL_CALL = "tool_call"
    REFLECTION = "reflection"
    PLANNING = "planning"
    RESPONSE = "response"

class ToolCall(BaseModel):
    """A tool call to be executed."""
    tool_name: str
    tool_input: Dict[str, Any]
    description: Optional[str] = None

class Thought(BaseModel):
    """Agent's internal thought process."""
    reasoning: str
    plan: List[str]
    next_action: str
    confidence: float  # 0-1 confidence in the plan

class Action(BaseModel):
    """An action taken by the agent."""
    type: ActionType
    tool_call: Optional[ToolCall] = None
    timestamp: datetime = field(default_factory=datetime.now)

class Observation(BaseModel):
    """Observation from executing an action."""
    action_type: ActionType
    result: str
    success: bool
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

class Reflection(BaseModel):
    """Agent's reflection on its actions."""
    observation: str
    analysis: str
    lessons_learned: List[str]
    adjustments: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class Task(BaseModel):
    """A task to be executed by the agent."""
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0  # Higher number = higher priority
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    subtasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)

class AgentState(BaseModel):
    """
    Complete state of the agent during execution.
    This is passed through the LangGraph workflow.
    """
    # Conversation and task context
    conversation_id: str
    user_message: str
    
    # Task management
    current_task: Optional[Task] = None
    task_list: List[Task] = field(default_factory=list)
    completed_tasks: List[Task] = field(default_factory=list)
    
    # Agent thinking and planning
    thought: Optional[Thought] = None
    plan: List[str] = field(default_factory=list)
    
    # Execution tracking
    actions: List[Action] = field(default_factory=list)
    observations: List[Observation] = field(default_factory=list)
    reflections: List[Reflection] = field(default_factory=list)
    
    # Error handling
    errors: List[Dict[str, Any]] = field(default_factory=list)
    error_count: int = 0
    last_error: Optional[str] = None
    
    # Iteration tracking
    iteration: int = 0
    max_iterations: int = 10
    
    # Context and memory
    context: Dict[str, Any] = field(default_factory=dict)
    memory_items: List[str] = field(default_factory=list)
    
    # Final response
    response: Optional[str] = None
    success: bool = False
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

class ConversationMessage(BaseModel):
    """A message in the conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConversationHistory(BaseModel):
    """History of a conversation."""
    conversation_id: str
    messages: List[ConversationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add a message to the conversation."""
        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_messages_for_llm(self) -> List[Dict[str, str]]:
        """Get messages in format suitable for LLM API."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

class ExecutionLog(BaseModel):
    """Log of agent execution."""
    conversation_id: str
    state: AgentState
    execution_time: float  # seconds
    token_usage: Optional[Dict[str, int]] = None
    success: bool
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

# Helper functions for state management

def create_initial_state(conversation_id: str, user_message: str) -> AgentState:
    """Create initial agent state for a new conversation."""
    return AgentState(
        conversation_id=conversation_id,
        user_message=user_message
    )

def update_state_with_thought(state: AgentState, thought: Thought) -> AgentState:
    """Update state with agent's thought."""
    state.thought = thought
    state.plan = thought.plan
    state.updated_at = datetime.now()
    return state

def update_state_with_action(state: AgentState, action: Action) -> AgentState:
    """Update state with an action."""
    state.actions.append(action)
    state.updated_at = datetime.now()
    return state

def update_state_with_observation(state: AgentState, observation: Observation) -> AgentState:
    """Update state with an observation."""
    state.observations.append(observation)
    if not observation.success:
        state.error_count += 1
        state.last_error = observation.error
        state.errors.append({
            "action": observation.action_type,
            "error": observation.error,
            "timestamp": observation.timestamp.isoformat()
        })
    state.updated_at = datetime.now()
    return state

def update_state_with_reflection(state: AgentState, reflection: Reflection) -> AgentState:
    """Update state with a reflection."""
    state.reflections.append(reflection)
    state.updated_at = datetime.now()
    return state

def increment_iteration(state: AgentState) -> AgentState:
    """Increment the iteration counter."""
    state.iteration += 1
    state.updated_at = datetime.now()
    return state
