"""
Enhanced Tool Manager with production-grade error handling, retry logic, and tool execution.
"""

import logging
import subprocess
import os
import json
import time
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ToolExecutionStatus(str, Enum):
    """Status of tool execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RETRY = "retry"

@dataclass
class ToolDefinition:
    """Definition of a tool available to the agent."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    requires_approval: bool = False
    max_retries: int = 3
    timeout: int = 30

@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    tool_name: str
    status: ToolExecutionStatus
    result: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    retries: int = 0
    timestamp: str = ""

class ToolManager:
    """
    Manages tools available to the agent.
    Handles registration, execution, error handling, and retry logic.
    """
    
    def __init__(self):
        """Initialize the tool manager."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.execution_history: List[ToolExecutionResult] = []
        self.max_execution_history: int = 1000
        self._register_default_tools()
        logger.info("Tool manager initialized")
    
    def _register_default_tools(self):
        """Register default tools available to the agent."""
        # Terminal execution tool
        self.register_tool(
            name="execute_command",
            description="Execute a shell command",
            parameters={
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30},
                "cwd": {"type": "string", "description": "Working directory", "default": "."}
            },
            handler=self._execute_command,
            requires_approval=True,
            max_retries=2,
            timeout=30
        )
        
        # File reading tool
        self.register_tool(
            name="read_file",
            description="Read contents of a file",
            parameters={
                "path": {"type": "string", "description": "Path to file"},
                "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                "chunk_size": {"type": "integer", "description": "Read in chunks (bytes)", "default": 0}
            },
            handler=self._read_file,
            requires_approval=False,
            max_retries=3,
            timeout=10
        )
        
        # File writing tool
        self.register_tool(
            name="write_file",
            description="Write contents to a file",
            parameters={
                "path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"},
                "mode": {"type": "string", "description": "Write mode (w/a)", "default": "w"},
                "create_backup": {"type": "boolean", "description": "Create backup", "default": True}
            },
            handler=self._write_file,
            requires_approval=True,
            max_retries=2,
            timeout=10
        )
        
        # Directory listing tool
        self.register_tool(
            name="list_directory",
            description="List contents of a directory",
            parameters={
                "path": {"type": "string", "description": "Directory path", "default": "."},
                "recursive": {"type": "boolean", "description": "Recursive listing", "default": False},
                "pattern": {"type": "string", "description": "File pattern filter", "default": "*"}
            },
            handler=self._list_directory,
            requires_approval=False,
            max_retries=2,
            timeout=10
        )
        
        # File deletion tool
        self.register_tool(
            name="delete_file",
            description="Delete a file",
            parameters={
                "path": {"type": "string", "description": "Path to file"},
                "force": {"type": "boolean", "description": "Force delete", "default": False}
            },
            handler=self._delete_file,
            requires_approval=True,
            max_retries=1,
            timeout=10
        )
        
        # Git clone tool
        self.register_tool(
            name="git_clone",
            description="Clone a GitHub repository",
            parameters={
                "repo_url": {"type": "string", "description": "Repository URL"},
                "target_path": {"type": "string", "description": "Target directory path"},
                "depth": {"type": "integer", "description": "Clone depth (0=full)", "default": 0}
            },
            handler=self._git_clone,
            requires_approval=True,
            max_retries=2,
            timeout=60
        )
        
        # Git commit tool
        self.register_tool(
            name="git_commit",
            description="Commit changes to a git repository",
            parameters={
                "path": {"type": "string", "description": "Repository path"},
                "message": {"type": "string", "description": "Commit message"},
                "author": {"type": "string", "description": "Author name", "default": "Manus Agent"}
            },
            handler=self._git_commit,
            requires_approval=True,
            max_retries=2,
            timeout=30
        )
        
        # Git push tool
        self.register_tool(
            name="git_push",
            description="Push changes to remote repository",
            parameters={
                "path": {"type": "string", "description": "Repository path"},
                "branch": {"type": "string", "description": "Branch name", "default": "main"},
                "force": {"type": "boolean", "description": "Force push", "default": False}
            },
            handler=self._git_push,
            requires_approval=True,
            max_retries=2,
            timeout=30
        )
        
        logger.info(f"Registered {len(self.tools)} default tools")
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
        requires_approval: bool = False,
        max_retries: int = 3,
        timeout: int = 30
    ):
        """Register a new tool."""
        tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            requires_approval=requires_approval,
            max_retries=max_retries,
            timeout=timeout
        )
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        user_approved: bool = True
    ) -> ToolExecutionResult:
        """
        Execute a tool with retry logic and error handling.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            user_approved: Whether user has approved execution
            
        Returns:
            ToolExecutionResult with execution details
        """
        if tool_name not in self.tools:
            result = ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.FAILED,
                error=f"Tool '{tool_name}' not found",
                timestamp=datetime.now().isoformat()
            )
            self.execution_history.append(result)
            return result
        
        tool = self.tools[tool_name]
        
        # Check approval requirement
        if tool.requires_approval and not user_approved:
            result = ToolExecutionResult(
                tool_name=tool_name,
                status=ToolExecutionStatus.FAILED,
                error=f"Tool '{tool_name}' requires user approval",
                timestamp=datetime.now().isoformat()
            )
            self.execution_history.append(result)
            return result
        
        # Execute with retry logic
        last_error = None
        for attempt in range(tool.max_retries):
            try:
                logger.info(f"Executing tool: {tool_name} (attempt {attempt + 1}/{tool.max_retries})")
                
                start_time = time.time()
                result_data = tool.handler(**tool_input)
                execution_time = time.time() - start_time
                
                result = ToolExecutionResult(
                    tool_name=tool_name,
                    status=ToolExecutionStatus.SUCCESS,
                    result=result_data,
                    execution_time=execution_time,
                    retries=attempt,
                    timestamp=datetime.now().isoformat()
                )
                
                self.execution_history.append(result)
                self._cleanup_history()
                
                logger.info(f"Tool {tool_name} executed successfully in {execution_time:.2f}s")
                return result
            
            except subprocess.TimeoutExpired as e:
                last_error = f"Tool timed out after {tool.timeout} seconds"
                logger.warning(f"Tool {tool_name} timed out (attempt {attempt + 1}): {last_error}")
                
                if attempt < tool.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Tool {tool_name} failed (attempt {attempt + 1}): {last_error}")
                
                if attempt < tool.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        # All retries exhausted
        result = ToolExecutionResult(
            tool_name=tool_name,
            status=ToolExecutionStatus.FAILED,
            error=last_error or "Tool execution failed",
            retries=tool.max_retries,
            timestamp=datetime.now().isoformat()
        )
        
        self.execution_history.append(result)
        self._cleanup_history()
        
        logger.error(f"Tool {tool_name} failed after {tool.max_retries} attempts: {last_error}")
        return result
    
    def get_tools_list(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "requires_approval": tool.requires_approval,
                "max_retries": tool.max_retries,
                "timeout": tool.timeout
            }
            for tool in self.tools.values()
        ]
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific tool."""
        if tool_name not in self.tools:
            return None
        
        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
            "requires_approval": tool.requires_approval,
            "max_retries": tool.max_retries,
            "timeout": tool.timeout
        }
    
    def get_execution_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tool execution history."""
        return [
            {
                "tool_name": r.tool_name,
                "status": r.status.value,
                "result": r.result[:200] if r.result else None,
                "error": r.error,
                "execution_time": r.execution_time,
                "retries": r.retries,
                "timestamp": r.timestamp
            }
            for r in self.execution_history[-limit:]
        ]
    
    def _cleanup_history(self):
        """Clean up execution history if it exceeds max size."""
        if len(self.execution_history) > self.max_execution_history:
            self.execution_history = self.execution_history[-self.max_execution_history:]
    
    # ========================================================================
    # Tool Implementations
    # ========================================================================
    
    def _execute_command(self, command: str, timeout: int = 30, cwd: str = ".") -> str:
        """Execute a shell command with proper error handling."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            
            if result.returncode != 0:
                raise Exception(f"Command failed with return code {result.returncode}: {result.stderr}")
            
            return output or "Command executed successfully"
        
        except subprocess.TimeoutExpired:
            raise subprocess.TimeoutExpired(command, timeout)
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
    
    def _read_file(self, path: str, encoding: str = "utf-8", chunk_size: int = 0) -> str:
        """Read file contents with support for large files."""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
            
            if chunk_size > 0:
                # Read in chunks for large files
                chunks = []
                with open(path, "r", encoding=encoding) as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        chunks.append(chunk)
                return "".join(chunks)
            else:
                # Read entire file
                with open(path, "r", encoding=encoding) as f:
                    return f.read()
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def _write_file(self, path: str, content: str, mode: str = "w", create_backup: bool = True) -> str:
        """Write content to a file with backup support."""
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            
            # Create backup if file exists
            if create_backup and os.path.exists(path) and mode == "w":
                backup_path = f"{path}.bak"
                with open(path, "r") as f:
                    backup_content = f.read()
                with open(backup_path, "w") as f:
                    f.write(backup_content)
                logger.info(f"Created backup: {backup_path}")
            
            with open(path, mode) as f:
                f.write(content)
            
            return f"Successfully wrote to {path}"
        except Exception as e:
            raise Exception(f"Error writing file: {str(e)}")
    
    def _list_directory(self, path: str = ".", recursive: bool = False, pattern: str = "*") -> str:
        """List directory contents with filtering."""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Directory not found: {path}")
            
            import glob
            
            if recursive:
                search_pattern = os.path.join(path, "**", pattern)
                items = glob.glob(search_pattern, recursive=True)
            else:
                search_pattern = os.path.join(path, pattern)
                items = glob.glob(search_pattern)
            
            return "\n".join(sorted(items))
        except Exception as e:
            raise Exception(f"Error listing directory: {str(e)}")
    
    def _delete_file(self, path: str, force: bool = False) -> str:
        """Delete a file with safety checks."""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
            
            if os.path.isfile(path):
                os.remove(path)
                return f"Successfully deleted {path}"
            else:
                raise Exception(f"Path is not a file: {path}")
        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}")
    
    def _git_clone(self, repo_url: str, target_path: str, depth: int = 0) -> str:
        """Clone a git repository."""
        try:
            os.makedirs(os.path.dirname(target_path) or ".", exist_ok=True)
            
            cmd = f"git clone"
            if depth > 0:
                cmd += f" --depth {depth}"
            cmd += f" {repo_url} {target_path}"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return f"Successfully cloned {repo_url}"
            else:
                raise Exception(result.stderr)
        except Exception as e:
            raise Exception(f"Error cloning repository: {str(e)}")
    
    def _git_commit(self, path: str, message: str, author: str = "Manus Agent") -> str:
        """Commit changes to git repository."""
        try:
            cmd = f"git -C {path} -c user.name='{author}' -c user.email='agent@manus.ai' add . && git -C {path} commit -m '{message}'"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return f"Successfully committed: {message}"
            else:
                raise Exception(result.stderr)
        except Exception as e:
            raise Exception(f"Error committing changes: {str(e)}")
    
    def _git_push(self, path: str, branch: str = "main", force: bool = False) -> str:
        """Push changes to remote repository."""
        try:
            cmd = f"git -C {path} push origin {branch}"
            if force:
                cmd += " --force"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return f"Successfully pushed to {branch}"
            else:
                raise Exception(result.stderr)
        except Exception as e:
            raise Exception(f"Error pushing changes: {str(e)}")

# Global tool manager instance
_tool_manager: Optional[ToolManager] = None

def get_tool_manager() -> ToolManager:
    """Get or create the global tool manager."""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager
