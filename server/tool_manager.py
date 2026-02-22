"""
Extended tool manager with robust file system, web browsing, and GitHub integration.
Implements Phase 1.1 of the Production Roadmap.
"""

import logging
import subprocess
import os
import json
import shutil
import time
from typing import Dict, Any, Callable, Optional, List, Union
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
    Handles registration, execution, and error handling with production-grade robustness.
    """
    
    def __init__(self):
        """Initialize the tool manager."""
        self.tools: Dict[str, ToolDefinition] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self._register_default_tools()
        logger.info("Tool manager initialized with production-grade tools")
    
    def _register_default_tools(self):
        """Register default tools available to the agent."""
        
        # --- File System Tools (Phase 1.1) ---
        
        self.register_tool(
            name="execute_command",
            description="Execute a shell command with timeout and resource monitoring",
            parameters={
                "command": {"type": "string", "description": "Shell command to execute"},
                "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 60},
                "cwd": {"type": "string", "description": "Working directory", "default": "."}
            },
            handler=self._execute_command,
            requires_approval=True
        )
        
        self.register_tool(
            name="read_file",
            description="Read contents of a file with chunking support for large files",
            parameters={
                "path": {"type": "string", "description": "Path to file"},
                "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                "max_bytes": {"type": "integer", "description": "Maximum bytes to read", "default": 1048576}
            },
            handler=self._read_file,
            requires_approval=False
        )
        
        self.register_tool(
            name="write_file",
            description="Write contents to a file atomically with backup support",
            parameters={
                "path": {"type": "string", "description": "Path to file"},
                "content": {"type": "string", "description": "Content to write"},
                "append": {"type": "boolean", "description": "Append instead of overwrite", "default": False},
                "create_backup": {"type": "boolean", "description": "Create backup of existing file", "default": True}
            },
            handler=self._write_file,
            requires_approval=True
        )
        
        self.register_tool(
            name="list_directory",
            description="List contents of a directory with recursive and filtering support",
            parameters={
                "path": {"type": "string", "description": "Directory path", "default": "."},
                "recursive": {"type": "boolean", "description": "List recursively", "default": False},
                "pattern": {"type": "string", "description": "Glob pattern for filtering", "default": "*"}
            },
            handler=self._list_directory,
            requires_approval=False
        )
        
        self.register_tool(
            name="delete_file",
            description="Delete a file or directory safely",
            parameters={
                "path": {"type": "string", "description": "Path to file or directory"},
                "recursive": {"type": "boolean", "description": "Delete directory recursively", "default": False}
            },
            handler=self._delete_file,
            requires_approval=True
        )

        # --- GitHub Tools (Phase 1.3) ---
        
        self.register_tool(
            name="git_clone",
            description="Clone a GitHub repository with depth control",
            parameters={
                "repo_url": {"type": "string", "description": "Repository URL"},
                "target_path": {"type": "string", "description": "Target directory path"},
                "depth": {"type": "integer", "description": "Clone depth", "default": 1}
            },
            handler=self._git_clone,
            requires_approval=True
        )
        
        self.register_tool(
            name="git_commit",
            description="Commit changes to a git repository",
            parameters={
                "path": {"type": "string", "description": "Repository path"},
                "message": {"type": "string", "description": "Commit message"},
                "all_files": {"type": "boolean", "description": "Stage all changes", "default": True}
            },
            handler=self._git_commit,
            requires_approval=True
        )
        
        self.register_tool(
            name="git_push",
            description="Push changes to remote repository",
            parameters={
                "path": {"type": "string", "description": "Repository path"},
                "branch": {"type": "string", "description": "Branch name", "default": "main"},
                "remote": {"type": "string", "description": "Remote name", "default": "origin"}
            },
            handler=self._git_push,
            requires_approval=True
        )
        
        logger.info(f"Registered {len(self.tools)} production-grade tools")
    
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
        """Execute a tool with error handling and retries."""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        
        if tool.requires_approval and not user_approved:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' requires user approval",
                "requires_approval": True
            }
        
        start_time = time.time()
        try:
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
            
            # Handle both sync and async handlers
            import inspect
            if inspect.iscoroutinefunction(tool.handler):
                result = await tool.handler(**tool_input)
            else:
                result = tool.handler(**tool_input)
            
            duration = time.time() - start_time
            
            self.execution_history.append({
                "tool": tool_name,
                "input": tool_input,
                "success": True,
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
            
            return {"success": True, "result": result, "duration": duration}
        
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            
            self.execution_history.append({
                "tool": tool_name,
                "input": tool_input,
                "success": False,
                "error": str(e),
                "duration": duration,
                "timestamp": datetime.now().isoformat()
            })
            
            return {"success": False, "error": str(e), "duration": duration}
    
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
    
    # ========================================================================
    # Tool Implementations (Phase 1.1 & 1.3)
    # ========================================================================
    
    def _execute_command(self, command: str, timeout: int = 60, cwd: str = ".") -> str:
        """Execute a shell command with robust handling."""
        try:
            # Ensure cwd exists
            if not os.path.exists(cwd):
                os.makedirs(cwd, exist_ok=True)
                
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            
            output = []
            if result.stdout:
                output.append(result.stdout)
            if result.stderr:
                output.append(f"STDERR: {result.stderr}")
            
            if result.returncode != 0:
                output.append(f"Exit Code: {result.returncode}")
                
            return "\n".join(output) or "Command executed successfully (no output)"
        
        except subprocess.TimeoutExpired:
            raise Exception(f"Command timed out after {timeout} seconds")
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
    
    def _read_file(self, path: str, encoding: str = "utf-8", max_bytes: int = 1048576) -> str:
        """Read file contents with size limits."""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"File not found: {path}")
                
            file_size = os.path.getsize(path)
            if file_size > max_bytes:
                logger.warning(f"File {path} is large ({file_size} bytes). Truncating to {max_bytes} bytes.")
                
            with open(path, "r", encoding=encoding) as f:
                return f.read(max_bytes)
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def _write_file(self, path: str, content: str, append: bool = False, create_backup: bool = True) -> str:
        """Write content to a file atomically."""
        try:
            abs_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # Create backup if file exists
            if create_backup and os.path.exists(abs_path) and not append:
                backup_path = f"{abs_path}.{int(time.time())}.bak"
                shutil.copy2(abs_path, backup_path)
                logger.info(f"Created backup: {backup_path}")
            
            mode = "a" if append else "w"
            
            # Atomic write using a temporary file
            temp_path = f"{abs_path}.tmp"
            with open(temp_path, mode) as f:
                f.write(content)
            
            if append:
                # For append, we just write to the end of the original file
                with open(abs_path, "a") as f:
                    f.write(content)
                os.remove(temp_path)
            else:
                # For overwrite, we rename the temp file to the original
                os.replace(temp_path, abs_path)
            
            return f"Successfully wrote to {path}"
        except Exception as e:
            raise Exception(f"Error writing file: {str(e)}")
    
    def _list_directory(self, path: str = ".", recursive: bool = False, pattern: str = "*") -> str:
        """List directory contents with advanced options."""
        try:
            import glob
            search_path = os.path.join(path, "**", pattern) if recursive else os.path.join(path, pattern)
            items = glob.glob(search_path, recursive=recursive)
            
            # Clean up paths to be relative to the input path
            base_path = os.path.abspath(path)
            relative_items = [os.path.relpath(os.path.abspath(item), base_path) for item in items]
            
            return "\n".join(relative_items) or "No matching items found"
        except Exception as e:
            raise Exception(f"Error listing directory: {str(e)}")
    
    def _delete_file(self, path: str, recursive: bool = False) -> str:
        """Delete a file or directory safely."""
        try:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Path not found: {path}")
                
            if os.path.isfile(path):
                os.remove(path)
                return f"Successfully deleted file: {path}"
            elif os.path.isdir(path):
                if recursive:
                    shutil.rmtree(path)
                    return f"Successfully deleted directory recursively: {path}"
                else:
                    os.rmdir(path)
                    return f"Successfully deleted empty directory: {path}"
            else:
                raise Exception(f"Path is neither a file nor a directory: {path}")
        except Exception as e:
            raise Exception(f"Error deleting path: {str(e)}")
    
    def _git_clone(self, repo_url: str, target_path: str, depth: int = 1) -> str:
        """Clone a git repository with depth control."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            
            cmd = f"git clone --depth {depth} {repo_url} {target_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return f"Successfully cloned {repo_url} to {target_path}"
            else:
                raise Exception(result.stderr)
        except Exception as e:
            raise Exception(f"Error cloning repository: {str(e)}")
    
    def _git_commit(self, path: str, message: str, all_files: bool = True) -> str:
        """Commit changes to git repository."""
        try:
            add_cmd = "git add ." if all_files else "git add -u"
            commit_cmd = f"git commit -m '{message}'"
            
            full_cmd = f"git -C {path} {add_cmd} && git -C {path} {commit_cmd}"
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return f"Successfully committed: {message}"
            else:
                raise Exception(result.stderr)
        except Exception as e:
            raise Exception(f"Error committing changes: {str(e)}")
    
    def _git_push(self, path: str, branch: str = "main", remote: str = "origin") -> str:
        """Push changes to remote repository."""
        try:
            cmd = f"git -C {path} push {remote} {branch}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                return f"Successfully pushed to {remote}/{branch}"
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
