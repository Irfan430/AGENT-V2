"""
Extended tool manager with web browsing and GitHub integration.
"""

import logging
import subprocess
import os
import json
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ToolDefinition:
    """Definition of a tool available to the agent."""
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable
    requires_approval: bool = False

class ToolManager:
    """
    Manages tools available to the agent.
    Handles registration, execution, and error handling.
    """
    
    def __init__(self):
        """Initialize the tool manager."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.execution_history: List[Dict[str, Any]] = []
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
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
            },
            handler=self._execute_command,
            requires_approval=True
        )
        
        # File reading tool
        self.register_tool(
            name="read_file",
            description="Read contents of a file",
            parameters={
                "path": {"type": "string", "description": "Path to file"},
                "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"}
            },
            handler=self._read_file,
            requires_approval=False
        )
        
        # File writing tool
        self.register_tool(
            name="write_file",
            description="Write contents to a file",
            parameters={
                "path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"},
                "mode": {"type": "string", "description": "Write mode", "default": "w"}
            },
            handler=self._write_file,
            requires_approval=True
        )
        
        # Directory listing tool
        self.register_tool(
            name="list_directory",
            description="List contents of a directory",
            parameters={
                "path": {"type": "string", "description": "Directory path", "default": "."}
            },
            handler=self._list_directory,
            requires_approval=False
        )
        
        # File deletion tool
        self.register_tool(
            name="delete_file",
            description="Delete a file",
            parameters={
                "path": {"type": "string", "description": "Path to file"}
            },
            handler=self._delete_file,
            requires_approval=True
        )
        
        # Git clone tool
        self.register_tool(
            name="git_clone",
            description="Clone a GitHub repository",
            parameters={
                "repo_url": {"type": "string", "description": "Repository URL"},
                "target_path": {"type": "string", "description": "Target directory path"}
            },
            handler=self._git_clone,
            requires_approval=True
        )
        
        # Git commit tool
        self.register_tool(
            name="git_commit",
            description="Commit changes to a git repository",
            parameters={
                "path": {"type": "string", "description": "Repository path"},
                "message": {"type": "string", "description": "Commit message"}
            },
            handler=self._git_commit,
            requires_approval=True
        )
        
        # Git push tool
        self.register_tool(
            name="git_push",
            description="Push changes to remote repository",
            parameters={
                "path": {"type": "string", "description": "Repository path"},
                "branch": {"type": "string", "description": "Branch name", "default": "main"}
            },
            handler=self._git_push,
            requires_approval=True
        )
        
        logger.info(f"Registered {len(self.tools)} default tools")
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
        requires_approval: bool = False
    ):
        """Register a new tool."""
        tool = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            requires_approval=requires_approval
        )
        self.tools[name] = tool
        logger.info(f"Registered tool: {name}")
    
    async def execute_tool(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        user_approved: bool = True
    ) -> Dict[str, Any]:
        """Execute a tool."""
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        tool = self.tools[tool_name]
        
        # Check approval requirement
        if tool.requires_approval and not user_approved:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' requires user approval",
                "requires_approval": True
            }
        
        try:
            logger.info(f"Executing tool: {tool_name}")
            result = tool.handler(**tool_input)
            
            # Record execution
            self.execution_history.append({
                "tool": tool_name,
                "input": tool_input,
                "success": True,
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": True,
                "result": result
            }
        
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            
            # Record execution
            self.execution_history.append({
                "tool": tool_name,
                "input": tool_input,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tools_list(self) -> List[Dict[str, Any]]:
        """Get list of available tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
                "requires_approval": tool.requires_approval
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
            "requires_approval": tool.requires_approval
        }
    
    # ========================================================================
    # Tool Implementations
    # ========================================================================
    
    def _execute_command(self, command: str, timeout: int = 30) -> str:
        """Execute a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR: {result.stderr}"
            
            return output or "Command executed successfully"
        
        except subprocess.TimeoutExpired:
            raise Exception(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
    
    def _read_file(self, path: str, encoding: str = "utf-8") -> str:
        """Read file contents."""
        try:
            with open(path, "r", encoding=encoding) as f:
                return f.read()
        except FileNotFoundError:
            raise Exception(f"File not found: {path}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def _write_file(self, path: str, content: str, mode: str = "w") -> str:
        """Write content to a file."""
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            with open(path, mode) as f:
                f.write(content)
            
            return f"Successfully wrote to {path}"
        except Exception as e:
            raise Exception(f"Error writing file: {str(e)}")
    
    def _list_directory(self, path: str = ".") -> str:
        """List directory contents."""
        try:
            items = os.listdir(path)
            return "\n".join(items)
        except FileNotFoundError:
            raise Exception(f"Directory not found: {path}")
        except Exception as e:
            raise Exception(f"Error listing directory: {str(e)}")
    
    def _delete_file(self, path: str) -> str:
        """Delete a file."""
        try:
            if os.path.isfile(path):
                os.remove(path)
                return f"Successfully deleted {path}"
            else:
                raise Exception(f"Path is not a file: {path}")
        except Exception as e:
            raise Exception(f"Error deleting file: {str(e)}")
    
    def _git_clone(self, repo_url: str, target_path: str) -> str:
        """Clone a git repository."""
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            result = subprocess.run(
                f"git clone {repo_url} {target_path}",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return f"Successfully cloned {repo_url}"
            else:
                raise Exception(result.stderr)
        except Exception as e:
            raise Exception(f"Error cloning repository: {str(e)}")
    
    def _git_commit(self, path: str, message: str) -> str:
        """Commit changes to git repository."""
        try:
            result = subprocess.run(
                f"git -C {path} add . && git -C {path} commit -m '{message}'",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return f"Successfully committed: {message}"
            else:
                raise Exception(result.stderr)
        except Exception as e:
            raise Exception(f"Error committing changes: {str(e)}")
    
    def _git_push(self, path: str, branch: str = "main") -> str:
        """Push changes to remote repository."""
        try:
            result = subprocess.run(
                f"git -C {path} push origin {branch}",
                shell=True,
                capture_output=True,
                text=True
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
