"""
Production-grade file system tools for AGENT-V2.
Implements Phase 1.1 of the Roadmap with robust error handling and safety checks.
"""

import os
import shutil
import subprocess
import logging
import hashlib
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class FileSystemTools:
    """
    Advanced file system operations with safety and reliability.
    """
    
    def __init__(self, base_path: str = "/home/ubuntu"):
        self.base_path = Path(base_path).resolve()
        logger.info(f"FileSystemTools initialized with base path: {self.base_path}")

    def _validate_path(self, path: Union[str, Path]) -> Path:
        """Ensure the path is within the allowed base directory."""
        resolved_path = Path(path).resolve()
        # For this personal agent, we allow access to /home/ubuntu and /tmp
        allowed_prefixes = [self.base_path, Path("/tmp").resolve()]
        
        is_allowed = any(str(resolved_path).startswith(str(prefix)) for prefix in allowed_prefixes)
        
        if not is_allowed:
            raise PermissionError(f"Access to path {path} is restricted.")
        return resolved_path

    async def execute_command(self, command: str, timeout: int = 60, cwd: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a shell command with timeout and error capture.
        """
        logger.info(f"Executing command: {command}")
        try:
            working_dir = self._validate_path(cwd) if cwd else self.base_path
            
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(working_dir)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                exit_code = process.returncode
                
                return {
                    "success": exit_code == 0,
                    "stdout": stdout.decode().strip(),
                    "stderr": stderr.decode().strip(),
                    "exit_code": exit_code
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": f"Command timed out after {timeout} seconds",
                    "exit_code": -1
                }
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return {"success": False, "error": str(e), "exit_code": -1}

    def read_file(self, path: str, encoding: str = "utf-8", chunk_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Read file content with encoding detection and chunking support.
        """
        try:
            file_path = self._validate_path(path)
            if not file_path.is_file():
                return {"success": False, "error": f"{path} is not a file"}
            
            # Basic large file check
            file_size = file_path.stat().st_size
            if file_size > 10 * 1024 * 1024 and not chunk_size: # 10MB limit for direct read
                return {"success": False, "error": "File too large for direct read. Use chunked reading."}

            with open(file_path, 'r', encoding=encoding) as f:
                if chunk_size:
                    content = f.read(chunk_size)
                else:
                    content = f.read()
            
            return {
                "success": True,
                "content": content,
                "size": file_size,
                "encoding": encoding
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def write_file(self, path: str, content: str, append: bool = False) -> Dict[str, Any]:
        """
        Write content to a file atomically using a temporary file.
        """
        try:
            file_path = self._validate_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            
            # Atomic write for non-append mode
            if not append:
                temp_path = file_path.with_suffix('.tmp')
                with open(temp_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                temp_path.replace(file_path)
            else:
                with open(file_path, 'a', encoding='utf-8') as f:
                    f.write(content)
            
            return {"success": True, "path": str(file_path), "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_directory(self, path: str = ".", recursive: bool = False) -> Dict[str, Any]:
        """
        List directory contents with metadata.
        """
        try:
            dir_path = self._validate_path(path)
            if not dir_path.is_dir():
                return {"success": False, "error": f"{path} is not a directory"}
            
            items = []
            pattern = "**/*" if recursive else "*"
            
            for p in dir_path.glob(pattern):
                items.append({
                    "name": p.name,
                    "path": str(p.relative_to(self.base_path)),
                    "is_dir": p.is_dir(),
                    "size": p.stat().st_size if p.is_file() else 0,
                    "modified": datetime.fromtimestamp(p.stat().st_mtime).isoformat()
                })
            
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_path(self, path: str, recursive: bool = False) -> Dict[str, Any]:
        """
        Delete a file or directory.
        """
        try:
            target_path = self._validate_path(path)
            if not target_path.exists():
                return {"success": False, "error": "Path does not exist"}
            
            if target_path.is_dir():
                if recursive:
                    shutil.rmtree(target_path)
                else:
                    target_path.rmdir()
            else:
                target_path.unlink()
            
            return {"success": True, "message": f"Deleted {path}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

import asyncio # Needed for execute_command
