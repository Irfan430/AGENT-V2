"""
Security and validation module for production-grade protection.
Handles input validation, rate limiting, and security checks.
"""

import logging
import re
import hashlib
import time
from typing import Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)

class SecurityLevel(str, Enum):
    """Security levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RateLimiter:
    """Rate limiter for API endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, identifier: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed.
        
        Args:
            identifier: Client identifier (IP, user ID, etc.)
            
        Returns:
            Tuple of (allowed, info_dict)
        """
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > cutoff
        ]
        
        # Check limit
        current_count = len(self.requests[identifier])
        allowed = current_count < self.max_requests
        
        if allowed:
            self.requests[identifier].append(now)
        
        info = {
            "allowed": allowed,
            "current_count": current_count,
            "max_requests": self.max_requests,
            "window_seconds": self.window_seconds,
            "remaining": max(0, self.max_requests - current_count)
        }
        
        return allowed, info

class InputValidator:
    """Validates and sanitizes user input."""
    
    # Patterns for common injection attacks
    SQL_INJECTION_PATTERN = re.compile(
        r"(\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        re.IGNORECASE
    )
    
    XSS_PATTERN = re.compile(
        r"(<script|javascript:|onerror=|onload=|onclick=|<iframe|<object|<embed)",
        re.IGNORECASE
    )
    
    COMMAND_INJECTION_PATTERN = re.compile(
        r"(;|&&|\||`|\$\(|>\s*&)"
    )
    
    # File path traversal patterns
    PATH_TRAVERSAL_PATTERN = re.compile(
        r"(\.\./|\.\.\\|%2e%2e/|%2e%2e\\)"
    )
    
    @staticmethod
    def validate_string(
        value: str,
        min_length: int = 1,
        max_length: int = 10000,
        allow_special_chars: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """Validate string input."""
        if not isinstance(value, str):
            return False, "Input must be a string"
        
        if len(value) < min_length:
            return False, f"Input too short (min: {min_length})"
        
        if len(value) > max_length:
            return False, f"Input too long (max: {max_length})"
        
        if not allow_special_chars and not value.isalnum():
            return False, "Special characters not allowed"
        
        return True, None
    
    @staticmethod
    def check_sql_injection(value: str) -> Tuple[bool, Optional[str]]:
        """Check for SQL injection patterns."""
        if InputValidator.SQL_INJECTION_PATTERN.search(value):
            return False, "Potential SQL injection detected"
        return True, None
    
    @staticmethod
    def check_xss(value: str) -> Tuple[bool, Optional[str]]:
        """Check for XSS patterns."""
        if InputValidator.XSS_PATTERN.search(value):
            return False, "Potential XSS attack detected"
        return True, None
    
    @staticmethod
    def check_command_injection(value: str) -> Tuple[bool, Optional[str]]:
        """Check for command injection patterns."""
        if InputValidator.COMMAND_INJECTION_PATTERN.search(value):
            return False, "Potential command injection detected"
        return True, None
    
    @staticmethod
    def check_path_traversal(value: str) -> Tuple[bool, Optional[str]]:
        """Check for path traversal patterns."""
        if InputValidator.PATH_TRAVERSAL_PATTERN.search(value):
            return False, "Potential path traversal detected"
        return True, None
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize string by removing dangerous characters."""
        # Remove null bytes
        value = value.replace('\x00', '')
        
        # Remove control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        return value
    
    @staticmethod
    def validate_command(command: str) -> Tuple[bool, Optional[str]]:
        """Validate shell command for safety."""
        # Check for dangerous patterns
        dangerous_commands = [
            "rm -rf",
            "dd if=",
            "fork()",
            ":(){:|:&};:",  # fork bomb
        ]
        
        for dangerous in dangerous_commands:
            if dangerous in command:
                return False, f"Dangerous command pattern detected: {dangerous}"
        
        # Check for injection patterns
        is_safe, error = InputValidator.check_command_injection(command)
        if not is_safe:
            return False, error
        
        return True, None
    
    @staticmethod
    def validate_file_path(path: str) -> Tuple[bool, Optional[str]]:
        """Validate file path for safety."""
        # Check for path traversal
        is_safe, error = InputValidator.check_path_traversal(path)
        if not is_safe:
            return False, error
        
        # Check for null bytes
        if '\x00' in path:
            return False, "Null bytes in path"
        
        return True, None

class SecurityAuditor:
    """Audits security-related events."""
    
    def __init__(self):
        """Initialize the security auditor."""
        self.audit_log: list = []
        self.security_events: Dict[str, int] = defaultdict(int)
        self.max_log_size = 10000
    
    def log_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """Log a security event."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity.value,
            "user_id": user_id,
            "details": details
        }
        
        self.audit_log.append(event)
        self.security_events[event_type] += 1
        
        # Cleanup if needed
        if len(self.audit_log) > self.max_log_size:
            self.audit_log = self.audit_log[-self.max_log_size:]
        
        logger.warning(f"Security event: {event_type} ({severity.value}) - {details}")
    
    def get_audit_log(self, limit: int = 100) -> list:
        """Get recent audit log entries."""
        return self.audit_log[-limit:]
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security event summary."""
        return {
            "total_events": len(self.audit_log),
            "event_types": dict(self.security_events),
            "recent_events": self.get_audit_log(10)
        }

class AuthenticationManager:
    """Manages API authentication and authorization."""
    
    def __init__(self):
        """Initialize the authentication manager."""
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("Authentication manager initialized")
    
    def generate_api_key(self, user_id: str, name: str = "default") -> str:
        """Generate a new API key."""
        import secrets
        
        key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        self.api_keys[key_hash] = {
            "user_id": user_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "active": True
        }
        
        logger.info(f"Generated API key for user: {user_id}")
        return key
    
    def validate_api_key(self, key: str) -> Tuple[bool, Optional[str]]:
        """Validate an API key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash not in self.api_keys:
            return False, "Invalid API key"
        
        key_info = self.api_keys[key_hash]
        
        if not key_info["active"]:
            return False, "API key is inactive"
        
        # Update last used time
        key_info["last_used"] = datetime.now().isoformat()
        
        return True, key_info["user_id"]
    
    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key."""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        if key_hash in self.api_keys:
            self.api_keys[key_hash]["active"] = False
            logger.info(f"Revoked API key")
            return True
        
        return False

class DataEncryption:
    """Handles data encryption and decryption."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return DataEncryption.hash_password(password) == password_hash
    
    @staticmethod
    def hash_data(data: str) -> str:
        """Hash data using SHA-256."""
        return hashlib.sha256(data.encode()).hexdigest()

# Global instances
_rate_limiter: Optional[RateLimiter] = None
_security_auditor: Optional[SecurityAuditor] = None
_auth_manager: Optional[AuthenticationManager] = None

def get_rate_limiter() -> RateLimiter:
    """Get or create the global rate limiter."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
    return _rate_limiter

def get_security_auditor() -> SecurityAuditor:
    """Get or create the global security auditor."""
    global _security_auditor
    if _security_auditor is None:
        _security_auditor = SecurityAuditor()
    return _security_auditor

def get_auth_manager() -> AuthenticationManager:
    """Get or create the global authentication manager."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthenticationManager()
    return _auth_manager
