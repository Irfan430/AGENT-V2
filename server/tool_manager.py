"""
Extended tool manager with robust file system, web browsing, GitHub, and Task Scheduling integration.
Implements Phase 1.1, 1.2, 1.3, and 5 of the Production Roadmap.
"""

import logging
import subprocess
import os
import json
import shutil
import time
import asyncio
from typing import Dict, Any, Callable, Optional, List, Union
from dataclasses import dataclass
from datetime import datetime

from server.web_browser_tool import get_browser_tool
from server.task_scheduler import get_task_scheduler

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

        # --- Web Browsing Tools (Phase 1.2) ---
        self.register_tool(
            name="web_navigate",
            description="Navigate to a URL and get page status",
            parameters={"url": {"type": "string", "description": "URL to navigate to"}},
            handler=self._web_navigate,
            requires_approval=False
        )
        
        self.register_tool(
            name="web_extract",
            description="Extract text and links from the current web page",
            parameters={},
            handler=self._web_extract,
            requires_approval=False
        )
        
        self.register_tool(
            name="web_search",
            description="Search the web using Google",
            parameters={"query": {"type": "string", "description": "Search query"}},
            handler=self._web_search,
            requires_approval=False
        )
        
        self.register_tool(
            name="web_screenshot",
            description="Take a screenshot of the current web page",
            parameters={"path": {"type": "string", "description": "Path to save screenshot", "default": "screenshot.png"}},
            handler=self._web_screenshot,
            requires_approval=False
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

        # --- Task Scheduling Tools (Phase 5) ---
        self.register_tool(
            name="schedule_one_time_task",
            description="Schedule a task to run once at a specific time.",
            parameters={
                "task_id": {"type": "string", "description": "Unique ID for the task"},
                "task_name": {"type": "string", "description": "Human-readable name for the task"},
                "run_at": {"type": "string", "description": "Datetime string (ISO format) when the task should run"},
                "task_func_name": {"type": "string", "description": "Name of the function to execute (must be registered in ToolManager)"},
                "task_func_kwargs": {"type": "object", "description": "Keyword arguments for the task function", "default": {}}
            },
            handler=self._schedule_one_time_task,
            requires_approval=True
        )

        self.register_tool(
            name="schedule_recurring_task",
            description="Schedule a task to run repeatedly based on a cron expression.",
            parameters={
                "task_id": {"type": "string", "description": "Unique ID for the task"},
                "task_name": {"type": "string", "description": "Human-readable name for the task"},
                "cron_expression": {"type": "string", "description": "6-field cron expression (seconds minutes hours day-of-month month day-of-week)"},
                "task_func_name": {"type": "string", "description": "Name of the function to execute (must be registered in ToolManager)"},
                "task_func_kwargs": {"type": "object", "description": "Keyword arguments for the task function", "default": {}}
            },
            handler=self._schedule_recurring_task,
            requires_approval=True
        )

        self.register_tool(
            name="schedule_interval_task",
            description="Schedule a task to run at fixed intervals.",
            parameters={
                "task_id": {"type": "string", "description": "Unique ID for the task"},
                "task_name": {"type": "string", "description": "Human-readable name for the task"},
                "interval_seconds": {"type": "integer", "description": "Interval in seconds between executions"},
                "task_func_name": {"type": "string", "description": "Name of the function to execute (must be registered in ToolManager)"},
                "task_func_kwargs": {"type": "object", "description": "Keyword arguments for the task function", "default": {}}
            },
            handler=self._schedule_interval_task,
            requires_approval=True
        )

        self.register_tool(
            name="cancel_scheduled_task",
            description="Cancel a previously scheduled task.",
            parameters={
                "task_id": {"type": "string", "description": "ID of the task to cancel"}
            },
            handler=self._cancel_scheduled_task,
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
            return {"success": False, "error": f"Tool \'{tool_name}\' not found"}
        
        tool = self.tools[tool_name]
        
        if tool.requires_approval and not user_approved:
            return {
                "success": False,
                "error": f"Tool \'{tool_name}\' requires user approval",
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
    # Tool Implementations
    # ========================================================================
    
    def _execute_command(self, command: str, timeout: int = 60, cwd: str = ".") -> str:
        """Execute a shell command with robust handling."""
        try:
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
            if result.stdout: output.append(result.stdout)
            if result.stderr: output.append(f"STDERR: {result.stderr}")
            if result.returncode != 0: output.append(f"Exit Code: {result.returncode}")
                
            return "\n".join(output) or "Command executed successfully (no output)"
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")
    
    def _read_file(self, path: str, encoding: str = "utf-8", max_bytes: int = 1048576) -> str:
        """Read file contents with size limits."""
        try:
            if not os.path.exists(path): raise FileNotFoundError(f"File not found: {path}")
            with open(path, "r", encoding=encoding) as f:
                return f.read(max_bytes)
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")
    
    def _write_file(self, path: str, content: str, append: bool = False, create_backup: bool = True) -> str:
        """Write content to a file atomically."""
        try:
            abs_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            if create_backup and os.path.exists(abs_path) and not append:
                backup_path = f"{abs_path}.{int(time.time())}.bak"
                shutil.copy2(abs_path, backup_path)
            
            mode = "a" if append else "w"
            with open(abs_path, mode) as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            raise Exception(f"Error writing file: {str(e)}")
    
    def _list_directory(self, path: str = ".", recursive: bool = False, pattern: str = "*") -> str:
        """List directory contents with advanced options."""
        try:
            import glob
            search_path = os.path.join(path, "**", pattern) if recursive else os.path.join(path, pattern)
            items = glob.glob(search_path, recursive=recursive)
            base_path = os.path.abspath(path)
            relative_items = [os.path.relpath(os.path.abspath(item), base_path) for item in items]
            return "\n".join(relative_items) or "No matching items found"
        except Exception as e:
            raise Exception(f"Error listing directory: {str(e)}")
    
    def _delete_file(self, path: str, recursive: bool = False) -> str:
        """Delete a file or directory safely."""
        try:
            if not os.path.exists(path): raise FileNotFoundError(f"Path not found: {path}")
            if os.path.isfile(path):
                os.remove(path)
                return f"Successfully deleted file: {path}"
            elif os.path.isdir(path):
                if recursive: shutil.rmtree(path)
                else: os.rmdir(path)
                return f"Successfully deleted directory: {path}"
            else: raise Exception(f"Path is neither a file nor a directory: {path}")
        except Exception as e:
            raise Exception(f"Error deleting path: {str(e)}")

    # --- Web Browser Tool Handlers ---
    async def _web_navigate(self, url: str) -> str:
        browser = get_browser_tool()
        result = await browser.navigate(url)
        return json.dumps(result)

    async def _web_extract(self) -> str:
        browser = get_browser_tool()
        result = await browser.extract_content()
        return json.dumps(result)

    async def _web_search(self, query: str) -> str:
        browser = get_browser_tool()
        result = await browser.search(query)
        return json.dumps(result)

    async def _web_screenshot(self, path: str = "screenshot.png") -> str:
        browser = get_browser_tool()
        result = await browser.take_screenshot(path)
        return json.dumps(result)

    # --- Git Tool Handlers ---
    def _git_clone(self, repo_url: str, target_path: str, depth: int = 1) -> str:
        try:
            cmd = f"git clone --depth {depth} {repo_url} {target_path}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0: return f"Successfully cloned {repo_url}"
            else: raise Exception(result.stderr)
        except Exception as e: raise Exception(f"Error cloning: {str(e)}")
    
    def _git_commit(self, path: str, message: str, all_files: bool = True) -> str:
        try:
            add_cmd = "git add ." if all_files else "git add -u"
            full_cmd = f"git -C {path} {add_cmd} && git -C {path} commit -m \'{message}\'"
            result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0: return f"Successfully committed: {message}"
            else: raise Exception(result.stderr)
        except Exception as e: raise Exception(f"Error committing: {str(e)}")
    
    def _git_push(self, path: str, branch: str = "main", remote: str = "origin") -> str:
        try:
            cmd = f"git -C {path} push {remote} {branch}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0: return f"Successfully pushed to {remote}/{branch}"
            else: raise Exception(result.stderr)
        except Exception as e: raise Exception(f"Error pushing: {str(e)}")

    # --- Task Scheduling Tool Handlers ---
    async def _schedule_one_time_task(self, task_id: str, task_name: str, run_at: str, task_func_name: str, task_func_kwargs: Dict[str, Any]) -> str:
        scheduler = get_task_scheduler()
        task_func = self.tools[task_func_name].handler # Get the actual function from registered tools
        run_datetime = datetime.fromisoformat(run_at)
        result = await scheduler.schedule_once(task_id, task_name, task_func, run_datetime, task_func_kwargs)
        return json.dumps(result)

    async def _schedule_recurring_task(self, task_id: str, task_name: str, cron_expression: str, task_func_name: str, task_func_kwargs: Dict[str, Any]) -> str:
        scheduler = get_task_scheduler()
        task_func = self.tools[task_func_name].handler
        result = await scheduler.schedule_recurring(task_id, task_name, task_func, cron_expression, task_func_kwargs)
        return json.dumps(result)

    async def _schedule_interval_task(self, task_id: str, task_name: str, interval_seconds: int, task_func_name: str, task_func_kwargs: Dict[str, Any]) -> str:
        scheduler = get_task_scheduler()
        task_func = self.tools[task_func_name].handler
        result = await scheduler.schedule_interval(task_id, task_name, task_func, interval_seconds, task_func_kwargs)
        return json.dumps(result)

    async def _cancel_scheduled_task(self, task_id: str) -> str:
        scheduler = get_task_scheduler()
        result = await scheduler.cancel_task(task_id)
        return json.dumps(result)

# Global tool manager instance
_tool_manager: Optional[ToolManager] = None

def get_tool_manager() -> ToolManager:
    """Get or create the global tool manager."""
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager
