"""
Production-grade GitHub tools for AGENT-V2.
Implements Phase 1.3 of the Roadmap with full Git and GitHub API integration.
"""

import os
import subprocess
import logging
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class GitHubTools:
    """
    Advanced Git and GitHub operations.
    """
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            # Use current working directory as base path
            base_path = os.getcwd()
        self.base_path = Path(base_path).resolve()
        logger.info(f"GitHubTools initialized with base path: {self.base_path}")

    def _run_git_command(self, args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Helper to run git commands."""
        try:
            working_dir = Path(cwd).resolve() if cwd else self.base_path
            
            result = subprocess.run(
                ["git"] + args,
                capture_output=True,
                text=True,
                cwd=str(working_dir),
                check=False
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }
        except Exception as e:
            logger.error(f"Git command failed: {str(e)}")
            return {"success": False, "error": str(e), "exit_code": -1}

    def git_clone(self, repo_url: str, dest_path: Optional[str] = None) -> Dict[str, Any]:
        """Clone a repository."""
        args = ["clone", repo_url]
        if dest_path:
            args.append(dest_path)
        
        return self._run_git_command(args)

    def git_status(self, repo_path: str) -> Dict[str, Any]:
        """Get git status."""
        return self._run_git_command(["status"], cwd=repo_path)

    def git_add(self, repo_path: str, files: Union[str, List[str]] = ".") -> Dict[str, Any]:
        """Add files to staging."""
        if isinstance(files, str):
            files = [files]
        return self._run_git_command(["add"] + files, cwd=repo_path)

    def git_commit(self, repo_path: str, message: str) -> Dict[str, Any]:
        """Commit changes."""
        return self._run_git_command(["commit", "-m", message], cwd=repo_path)

    def git_push(self, repo_path: str, remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
        """Push changes."""
        return self._run_git_command(["push", remote, branch], cwd=repo_path)

    def git_pull(self, repo_path: str, remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
        """Pull changes."""
        return self._run_git_command(["pull", remote, branch], cwd=repo_path)

    def git_branch(self, repo_path: str, branch_name: str, create: bool = False) -> Dict[str, Any]:
        """Manage branches."""
        if create:
            return self._run_git_command(["checkout", "-b", branch_name], cwd=repo_path)
        else:
            return self._run_git_command(["checkout", branch_name], cwd=repo_path)

    def git_log(self, repo_path: str, n: int = 5) -> Dict[str, Any]:
        """Get git log."""
        return self._run_git_command(["log", f"-n {n}", "--oneline"], cwd=repo_path)

    def github_repo_create(self, name: str, private: bool = True, description: str = "") -> Dict[str, Any]:
        """Create a new GitHub repository using gh CLI."""
        try:
            args = ["gh", "repo", "create", name, "--description", description]
            if private:
                args.append("--private")
            else:
                args.append("--public")
            
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=False
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def github_issue_create(self, repo: str, title: str, body: str) -> Dict[str, Any]:
        """Create a GitHub issue."""
        try:
            result = subprocess.run(
                ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body],
                capture_output=True,
                text=True,
                check=False
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip()
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
