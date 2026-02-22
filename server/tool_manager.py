"""
Production-grade Tool Manager for AGENT-V2.
Orchestrates all tools (File, Web, Git, Scheduling) with a unified interface.
Implements Phase 1 and Phase 5 of the Production Roadmap.
"""

import logging
import json
import time
import inspect
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass
from datetime import datetime

from server.file_tools import FileSystemTools
from server.web_browser_tool import get_browser_tool
from server.github_tools import GitHubTools
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
    Manages and executes all available tools for the agent.
    """
    
    def __init__(self):
        self.file_tools = FileSystemTools()
        self.github_tools = GitHubTools()
        self.browser_tool = get_browser_tool()
        self.tools: Dict[str, ToolDefinition] = {}
        self._register_tools()
        logger.info("ToolManager initialized with all production tools")

    def _register_tools(self):
        """Register all available tools."""
        
        # File System Tools
        self.register_tool(
            name="execute_command",
            description="Execute a shell command with timeout and resource monitoring",
            parameters={"command": "string", "timeout": "integer", "cwd": "string"},
            handler=self.file_tools.execute_command,
            requires_approval=True
        )
        self.register_tool(
            name="read_file",
            description="Read contents of a file with chunking support",
            parameters={"path": "string", "encoding": "string", "chunk_size": "integer"},
            handler=self.file_tools.read_file
        )
        self.register_tool(
            name="write_file",
            description="Write contents to a file atomically",
            parameters={"path": "string", "content": "string", "append": "boolean"},
            handler=self.file_tools.write_file,
            requires_approval=True
        )
        self.register_tool(
            name="list_directory",
            description="List contents of a directory with recursive support",
            parameters={"path": "string", "recursive": "boolean"},
            handler=self.file_tools.list_directory
        )
        self.register_tool(
            name="delete_path",
            description="Delete a file or directory safely",
            parameters={"path": "string", "recursive": "boolean"},
            handler=self.file_tools.delete_path,
            requires_approval=True
        )

        # Web Browsing Tools
        self.register_tool(
            name="navigate_web",
            description="Navigate to a URL and get page status",
            parameters={"url": "string", "wait_until": "string"},
            handler=self.browser_tool.navigate
        )
        self.register_tool(
            name="web_search",
            description="Search the web using Google",
            parameters={"query": "string"},
            handler=self.browser_tool.search
        )
        self.register_tool(
            name="extract_web_content",
            description="Extract text and links from the current web page",
            parameters={},
            handler=self.browser_tool.extract_content
        )
        self.register_tool(
            name="take_screenshot",
            description="Take a screenshot of the current web page",
            parameters={"path": "string", "full_page": "boolean"},
            handler=self.browser_tool.take_screenshot
        )

        # GitHub Tools
        self.register_tool(
            name="git_clone",
            description="Clone a GitHub repository",
            parameters={"repo_url": "string", "dest_path": "string"},
            handler=self.github_tools.git_clone,
            requires_approval=True
        )
        self.register_tool(
            name="github_repo_create",
            description="Create a new GitHub repository",
            parameters={"name": "string", "private": "boolean", "description": "string"},
            handler=self.github_tools.github_repo_create,
            requires_approval=True
        )

        # Task Scheduling Tools (Phase 5)
        scheduler = get_task_scheduler()
        self.register_tool(
            name="schedule_once",
            description="Schedule a task to run once at a specific time",
            parameters={"task_id": "string", "task_name": "string", "run_at": "string", "task_func_name": "string", "task_func_kwargs": "object"},
            handler=scheduler.schedule_once,
            requires_approval=True
        )

    def register_tool(self, name: str, description: str, parameters: Dict[str, Any], handler: Callable, requires_approval: bool = False):
        """Register a new tool."""
        self.tools[name] = ToolDefinition(name=name, description=description, parameters=parameters, handler=handler, requires_approval=requires_approval)

    def get_tools_list(self) -> List[Dict[str, Any]]:
        """Return a list of all available tools for the LLM."""
        return [{"name": t.name, "description": t.description, "parameters": t.parameters, "requires_approval": t.requires_approval} for t in self.tools.values()]

    async def execute_tool(self, tool_name: str, tool_input: Dict[str, Any], user_approved: bool = True) -> Dict[str, Any]:
        """Execute a tool by name with the given input."""
        if tool_name not in self.tools:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        tool = self.tools[tool_name]
        
        if tool.requires_approval and not user_approved:
            return {"success": False, "error": f"Tool '{tool_name}' requires user approval", "requires_approval": True}
        
        try:
            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")
            if inspect.iscoroutinefunction(tool.handler):
                result = await tool.handler(**tool_input)
            else:
                result = tool.handler(**tool_input)
            
            return {"success": True, "result": result}
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {str(e)}")
            return {"success": False, "error": str(e)}

# Global instance
_tool_manager = None

def get_tool_manager() -> ToolManager:
    global _tool_manager
    if _tool_manager is None:
        _tool_manager = ToolManager()
    return _tool_manager
