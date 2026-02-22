"""
Agent configuration and system prompt setup.
Defines the agent's identity, capabilities, and behavior.
"""

from typing import Optional

# Agent Identity
AGENT_NAME = "Manus Agent Pro"
AGENT_VERSION = "1.0.0"
AGENT_DESCRIPTION = "An autonomous AI agent with deep OS interaction, web navigation, and code generation capabilities."

# System Prompt - Defines agent behavior and personality
SYSTEM_PROMPT = """You are {agent_name}, an advanced autonomous AI agent. You are designed to:

1. **Think Strategically**: Break down complex tasks into manageable steps and plan your approach.
2. **Act Autonomously**: Execute tasks using available tools without requiring constant human guidance.
3. **Learn & Adapt**: Reflect on your actions, learn from errors, and improve your approach.
4. **Communicate Clearly**: Explain your reasoning, provide updates, and ask for clarification when needed.

## Your Capabilities:
- Execute terminal commands and manage files
- Browse the web and interact with websites
- Create and manage GitHub repositories
- Analyze images and process multimedia
- Schedule tasks and execute them in parallel
- Access long-term memory for context and learning

## Your Operating Principles:
- **Safety First**: Always ask for approval before executing high-risk operations (deleting files, making API calls, etc.)
- **Transparency**: Explain what you're doing and why
- **Error Handling**: When you encounter errors, analyze them, reflect on the cause, and propose solutions
- **Continuous Learning**: Store important information in memory for future reference

## Your Workflow:
1. **Thought**: Analyze the task and plan your approach
2. **Action**: Execute the planned steps using available tools
3. **Observation**: Observe the results and any errors
4. **Reflection**: Reflect on what happened and adjust your approach if needed

	Remember: You are autonomous but not reckless. Always consider the implications of your actions and seek human approval for critical operations.

	## Personality:
	- You are professional, efficient, and helpful.
	- You speak with confidence but remain humble.
	- You provide concise but comprehensive answers.
	- When performing technical tasks, you explain the logic behind your choices.
	- You always maintain a supportive and proactive attitude.
	"""

# LLM Configuration
class LLMConfig:
    """Configuration for the language model."""
    
    model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 0.95
    
    # API Configuration
    api_base: str = "https://api.deepseek.com"
    api_key: Optional[str] = None  # Will be loaded from environment
    
    # Timeout and retry settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 2  # seconds

# Agent State Configuration
class AgentStateConfig:
    """Configuration for agent state management."""
    
    max_iterations: int = 10  # Maximum iterations in the agentic loop
    max_memory_items: int = 1000  # Maximum items in vector database
    memory_chunk_size: int = 1000  # Characters per chunk for embeddings
    memory_overlap: int = 100  # Character overlap between chunks
    
    # Reflection settings
    enable_reflection: bool = True
    reflection_threshold: int = 2  # Number of errors before triggering reflection
    max_consecutive_errors: int = 5  # Maximum consecutive errors before aborting
    
    # Context compression
    enable_context_compression: bool = True
    context_threshold: int = 8000  # Tokens before compression

# Tool Configuration
class ToolConfig:
    """Configuration for available tools."""
    
    # Terminal execution
    enable_terminal: bool = True
    max_command_timeout: int = 30  # seconds
    
    # File operations
    enable_file_ops: bool = True
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: list = ["py", "txt", "json", "yaml", "md", "js", "ts", "jsx", "tsx"]
    
    # Web browsing
    enable_web_browsing: bool = True
    headless_browser: bool = True
    browser_timeout: int = 30  # seconds
    
    # GitHub integration
    enable_github: bool = True
    
    # Image analysis
    enable_image_analysis: bool = True
    
    # Audio transcription
    enable_audio_transcription: bool = True
    
    # Task scheduling
    enable_scheduling: bool = True
    
    # Parallel execution
    enable_parallel_execution: bool = True
    max_parallel_tasks: int = 4

# Security Configuration
class SecurityConfig:
    """Configuration for security and sandboxing."""
    
    # Approval gates for high-risk operations
    require_approval_for: [
        "delete_file",
        "execute_command",  # Only for dangerous commands
        "create_repo",
        "push_to_github",
        "modify_system_files"
    ]
    
    # Workspace isolation
    workspace_root: str = "/home/ubuntu/agent_workspace"
    allow_outside_workspace: bool = False
    
    # Resource limits
    max_memory_usage: int = 2 * 1024 * 1024 * 1024  # 2GB
    max_cpu_usage: float = 80.0  # percentage
    max_disk_usage: int = 10 * 1024 * 1024 * 1024  # 10GB

# Memory Configuration
class MemoryConfig:
    """Configuration for ChromaDB and vector storage."""
    
    db_path: str = "./chroma_db"
    embedding_model: str = "all-MiniLM-L6-v2"
    similarity_threshold: float = 0.7
    max_results: int = 5  # Number of similar items to retrieve

# Notification Configuration
class NotificationConfig:
    """Configuration for notifications."""
    
    enable_notifications: bool = True
    notify_on_completion: bool = True
    notify_on_error: bool = True
    notify_on_approval_needed: bool = True
    notification_timeout: int = 300  # seconds

def get_system_prompt(agent_name: str = AGENT_NAME) -> str:
    """Get the formatted system prompt."""
    return SYSTEM_PROMPT.format(agent_name=agent_name)
