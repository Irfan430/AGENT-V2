"""
GitHub integration tool for repository management and version control.
Enables the agent to create repos, commit, push, and manage GitHub operations.
"""

import logging
import subprocess
import os
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class GitHubTool:
    """
    GitHub integration tool using git CLI and GitHub API.
    Provides repository management and version control capabilities.
    """
    
    def __init__(self, github_token: Optional[str] = None):
        """
        Initialize the GitHub tool.
        
        Args:
            github_token: GitHub personal access token
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        logger.info("GitHub tool initialized")
    
    def execute_git_command(self, command: str, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a git command.
        
        Args:
            command: Git command to execute
            cwd: Working directory
            
        Returns:
            Command result
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=cwd
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        
        except Exception as e:
            logger.error(f"Error executing git command: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def clone_repository(self, repo_url: str, target_path: str) -> Dict[str, Any]:
        """
        Clone a GitHub repository.
        
        Args:
            repo_url: Repository URL
            target_path: Target directory path
            
        Returns:
            Clone result
        """
        try:
            # Create parent directory if needed
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            
            command = f"git clone {repo_url} {target_path}"
            result = self.execute_git_command(command)
            
            if result["success"]:
                logger.info(f"Cloned repository: {repo_url}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error cloning repository: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def initialize_repository(self, path: str) -> Dict[str, Any]:
        """
        Initialize a new git repository.
        
        Args:
            path: Repository path
            
        Returns:
            Initialization result
        """
        try:
            os.makedirs(path, exist_ok=True)
            command = "git init"
            result = self.execute_git_command(command, cwd=path)
            
            if result["success"]:
                logger.info(f"Initialized repository: {path}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error initializing repository: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_files(self, path: str, files: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Add files to git staging area.
        
        Args:
            path: Repository path
            files: List of files to add (None for all)
            
        Returns:
            Add result
        """
        try:
            if files:
                command = f"git add {' '.join(files)}"
            else:
                command = "git add ."
            
            result = self.execute_git_command(command, cwd=path)
            
            if result["success"]:
                logger.info(f"Added files to staging area")
            
            return result
        
        except Exception as e:
            logger.error(f"Error adding files: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def commit(self, path: str, message: str, author_name: Optional[str] = None, 
               author_email: Optional[str] = None) -> Dict[str, Any]:
        """
        Commit changes to git repository.
        
        Args:
            path: Repository path
            message: Commit message
            author_name: Author name
            author_email: Author email
            
        Returns:
            Commit result
        """
        try:
            # Set git config if provided
            if author_name:
                self.execute_git_command(f"git config user.name '{author_name}'", cwd=path)
            if author_email:
                self.execute_git_command(f"git config user.email '{author_email}'", cwd=path)
            
            command = f"git commit -m '{message}'"
            result = self.execute_git_command(command, cwd=path)
            
            if result["success"]:
                logger.info(f"Committed changes: {message}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error committing changes: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def push(self, path: str, branch: str = "main", remote: str = "origin") -> Dict[str, Any]:
        """
        Push changes to remote repository.
        
        Args:
            path: Repository path
            branch: Branch to push
            remote: Remote name
            
        Returns:
            Push result
        """
        try:
            command = f"git push {remote} {branch}"
            result = self.execute_git_command(command, cwd=path)
            
            if result["success"]:
                logger.info(f"Pushed to {remote}/{branch}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error pushing changes: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_branch(self, path: str, branch_name: str) -> Dict[str, Any]:
        """
        Create a new branch.
        
        Args:
            path: Repository path
            branch_name: Branch name
            
        Returns:
            Branch creation result
        """
        try:
            command = f"git checkout -b {branch_name}"
            result = self.execute_git_command(command, cwd=path)
            
            if result["success"]:
                logger.info(f"Created branch: {branch_name}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error creating branch: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_status(self, path: str) -> Dict[str, Any]:
        """
        Get repository status.
        
        Args:
            path: Repository path
            
        Returns:
            Repository status
        """
        try:
            command = "git status --porcelain"
            result = self.execute_git_command(command, cwd=path)
            
            if result["success"]:
                files = result["stdout"].strip().split("\n") if result["stdout"] else []
                return {
                    "success": True,
                    "files": files
                }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_log(self, path: str, limit: int = 10) -> Dict[str, Any]:
        """
        Get commit log.
        
        Args:
            path: Repository path
            limit: Number of commits to retrieve
            
        Returns:
            Commit log
        """
        try:
            command = f"git log -n {limit} --oneline"
            result = self.execute_git_command(command, cwd=path)
            
            if result["success"]:
                commits = result["stdout"].strip().split("\n") if result["stdout"] else []
                return {
                    "success": True,
                    "commits": commits
                }
            
            return result
        
        except Exception as e:
            logger.error(f"Error getting log: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_pull_request(self, repo: str, title: str, body: str, 
                           head: str, base: str = "main") -> Dict[str, Any]:
        """
        Create a pull request using GitHub CLI.
        
        Args:
            repo: Repository in format owner/repo
            title: PR title
            body: PR description
            head: Head branch
            base: Base branch
            
        Returns:
            PR creation result
        """
        try:
            if not self.github_token:
                return {
                    "success": False,
                    "error": "GitHub token not configured"
                }
            
            # Use gh CLI for PR creation
            command = f"gh pr create --repo {repo} --title '{title}' --body '{body}' --head {head} --base {base}"
            
            env = os.environ.copy()
            env["GH_TOKEN"] = self.github_token
            
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                env=env
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        
        except Exception as e:
            logger.error(f"Error creating pull request: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

# Global GitHub tool instance
_github_tool: Optional[GitHubTool] = None

def get_github_tool(github_token: Optional[str] = None) -> GitHubTool:
    """Get or create the global GitHub tool."""
    global _github_tool
    if _github_tool is None:
        _github_tool = GitHubTool(github_token=github_token)
    return _github_tool
