"""
Enhanced GitHub tools for AGENT-V2 with full gh CLI integration.
Supports: clone, push, pull, create repos, manage issues, and more.
"""
import os
import subprocess
import logging
import json
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

logger = logging.getLogger(__name__)


class EnhancedGitHubTools:
    """
    Advanced Git and GitHub operations with gh CLI integration.
    Automatically detects gh CLI authentication.
    """

    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.getcwd()
        self.base_path = Path(base_path).resolve()
        self.gh_available = self._check_gh_cli()
        logger.info(f"EnhancedGitHubTools initialized (gh CLI: {'✓' if self.gh_available else '✗'})")

    def _check_gh_cli(self) -> bool:
        """Check if gh CLI is available and authenticated."""
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"gh CLI not available: {str(e)}")
            return False

    def _run_command(self, args: List[str], cwd: Optional[str] = None) -> Dict[str, Any]:
        """Helper to run shell commands."""
        try:
            working_dir = Path(cwd).resolve() if cwd else self.base_path
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                cwd=str(working_dir),
                check=False,
                timeout=30
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timeout", "exit_code": -1}
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return {"success": False, "error": str(e), "exit_code": -1}

    # ============================================================
    # Git Operations
    # ============================================================

    def git_clone(self, repo_url: str, dest_path: Optional[str] = None) -> Dict[str, Any]:
        """Clone a repository."""
        args = ["git", "clone", repo_url]
        if dest_path:
            args.append(dest_path)
        return self._run_command(args)

    def git_status(self, repo_path: str) -> Dict[str, Any]:
        """Get git status."""
        return self._run_command(["git", "status", "--porcelain"], cwd=repo_path)

    def git_add(self, repo_path: str, files: Union[str, List[str]] = ".") -> Dict[str, Any]:
        """Add files to staging."""
        if isinstance(files, str):
            files = [files]
        return self._run_command(["git", "add"] + files, cwd=repo_path)

    def git_commit(self, repo_path: str, message: str, author_name: Optional[str] = None, author_email: Optional[str] = None) -> Dict[str, Any]:
        """Commit changes with optional author info."""
        args = ["git", "commit", "-m", message]
        if author_name and author_email:
            args.extend(["--author", f"{author_name} <{author_email}>"])
        return self._run_command(args, cwd=repo_path)

    def git_push(self, repo_path: str, remote: str = "origin", branch: str = "main", force: bool = False) -> Dict[str, Any]:
        """Push changes."""
        args = ["git", "push", remote, branch]
        if force:
            args.insert(2, "-f")
        return self._run_command(args, cwd=repo_path)

    def git_pull(self, repo_path: str, remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
        """Pull changes."""
        return self._run_command(["git", "pull", remote, branch], cwd=repo_path)

    def git_branch(self, repo_path: str, branch_name: str, create: bool = False, delete: bool = False) -> Dict[str, Any]:
        """Manage branches."""
        if delete:
            return self._run_command(["git", "branch", "-d", branch_name], cwd=repo_path)
        elif create:
            return self._run_command(["git", "checkout", "-b", branch_name], cwd=repo_path)
        else:
            return self._run_command(["git", "checkout", branch_name], cwd=repo_path)

    def git_log(self, repo_path: str, n: int = 5, format: str = "oneline") -> Dict[str, Any]:
        """Get git log."""
        args = ["git", "log", f"-n {n}"]
        if format == "oneline":
            args.append("--oneline")
        elif format == "json":
            args.append("--format=%H|%an|%ae|%ad|%s")
        return self._run_command(args, cwd=repo_path)

    def git_diff(self, repo_path: str, staged: bool = False) -> Dict[str, Any]:
        """Get git diff."""
        args = ["git", "diff"]
        if staged:
            args.append("--staged")
        return self._run_command(args, cwd=repo_path)

    # ============================================================
    # GitHub Operations (via gh CLI)
    # ============================================================

    def github_repo_create(self, name: str, private: bool = True, description: str = "", source_path: Optional[str] = None) -> Dict[str, Any]:
        """Create a new GitHub repository."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available or not authenticated"}

        args = ["gh", "repo", "create", name]
        if description:
            args.extend(["--description", description])
        args.append("--private" if private else "--public")

        result = self._run_command(args)

        # If source path provided, initialize git and push
        if result["success"] and source_path:
            source_path = Path(source_path).resolve()
            if source_path.exists():
                # Initialize git if not already
                init_result = self._run_command(["git", "init"], cwd=str(source_path))
                if init_result["success"]:
                    # Add remote and push
                    repo_url = f"https://github.com/{self._get_github_user()}/{name}.git"
                    self._run_command(["git", "remote", "add", "origin", repo_url], cwd=str(source_path))
                    self._run_command(["git", "add", "."], cwd=str(source_path))
                    self._run_command(["git", "commit", "-m", "Initial commit"], cwd=str(source_path))
                    push_result = self._run_command(["git", "push", "-u", "origin", "main"], cwd=str(source_path))
                    if push_result["success"]:
                        result["pushed"] = True
                        result["repo_url"] = repo_url

        return result

    def github_repo_delete(self, repo: str, confirm: bool = False) -> Dict[str, Any]:
        """Delete a GitHub repository."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        args = ["gh", "repo", "delete", repo]
        if confirm:
            args.append("--confirm")

        return self._run_command(args)

    def github_issue_create(self, repo: str, title: str, body: str = "") -> Dict[str, Any]:
        """Create a GitHub issue."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        args = ["gh", "issue", "create", "--repo", repo, "--title", title]
        if body:
            args.extend(["--body", body])

        return self._run_command(args)

    def github_issue_list(self, repo: str, state: str = "open") -> Dict[str, Any]:
        """List GitHub issues."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        args = ["gh", "issue", "list", "--repo", repo, "--state", state, "--json", "number,title,state"]

        return self._run_command(args)

    def github_pr_create(self, repo: str, title: str, body: str = "", head: str = "main", base: str = "main") -> Dict[str, Any]:
        """Create a GitHub pull request."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        args = ["gh", "pr", "create", "--repo", repo, "--title", title, "--head", head, "--base", base]
        if body:
            args.extend(["--body", body])

        return self._run_command(args)

    def github_pr_list(self, repo: str, state: str = "open") -> Dict[str, Any]:
        """List GitHub pull requests."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        args = ["gh", "pr", "list", "--repo", repo, "--state", state, "--json", "number,title,state"]

        return self._run_command(args)

    def github_release_create(self, repo: str, tag: str, title: str = "", notes: str = "") -> Dict[str, Any]:
        """Create a GitHub release."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        args = ["gh", "release", "create", tag, "--repo", repo]
        if title:
            args.extend(["--title", title])
        if notes:
            args.extend(["--notes", notes])

        return self._run_command(args)

    def github_workflow_run(self, repo: str, workflow: str) -> Dict[str, Any]:
        """Trigger a GitHub Actions workflow."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        args = ["gh", "workflow", "run", workflow, "--repo", repo]

        return self._run_command(args)

    # ============================================================
    # Utility Methods
    # ============================================================

    def _get_github_user(self) -> str:
        """Get current GitHub user."""
        result = self._run_command(["gh", "api", "user", "-q", ".login"])
        if result["success"]:
            return result["stdout"]
        return "unknown"

    def get_github_user(self) -> Dict[str, Any]:
        """Get current GitHub user info."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        result = self._run_command(["gh", "api", "user"])
        if result["success"]:
            try:
                user_data = json.loads(result["stdout"])
                return {"success": True, "user": user_data}
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse user data"}

        return result

    def get_repo_info(self, repo: str) -> Dict[str, Any]:
        """Get repository information."""
        if not self.gh_available:
            return {"success": False, "error": "gh CLI not available"}

        args = ["gh", "repo", "view", repo, "--json", "name,description,url,isPrivate,stars"]

        result = self._run_command(args)
        if result["success"]:
            try:
                repo_data = json.loads(result["stdout"])
                return {"success": True, "repo": repo_data}
            except json.JSONDecodeError:
                return {"success": False, "error": "Failed to parse repo data"}

        return result


# Global instance
_github_tools = None


def get_github_tools() -> EnhancedGitHubTools:
    """Get or create the global GitHub tools instance."""
    global _github_tools
    if _github_tools is None:
        _github_tools = EnhancedGitHubTools()
    return _github_tools
