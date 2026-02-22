"""
Advanced error handling and self-correction system.
Classifies errors, suggests recovery strategies, and learns from failures.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorType(str, Enum):
    """Types of errors that can occur."""
    TOOL_EXECUTION = "tool_execution"
    LLM_API = "llm_api"
    MEMORY = "memory"
    NETWORK = "network"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    PERMISSION = "permission"
    RESOURCE = "resource"
    UNKNOWN = "unknown"

class RecoveryStrategy(str, Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK_TOOL = "fallback_tool"
    ADJUST_PARAMS = "adjust_params"
    SKIP_STEP = "skip_step"
    ABORT = "abort"
    MANUAL_INTERVENTION = "manual_intervention"

class ErrorClassification:
    """Classification of an error."""
    
    def __init__(
        self,
        error_message: str,
        error_type: ErrorType,
        severity: ErrorSeverity,
        recovery_strategy: RecoveryStrategy,
        suggested_action: str
    ):
        self.error_message = error_message
        self.error_type = error_type
        self.severity = severity
        self.recovery_strategy = recovery_strategy
        self.suggested_action = suggested_action
        self.timestamp = datetime.now().isoformat()

class ErrorHandler:
    """
    Advanced error handling system with classification and recovery.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_patterns: Dict[str, Dict[str, Any]] = {}
        self.error_history: List[ErrorClassification] = []
        self.recovery_success_rate: Dict[str, float] = {}
        logger.info("Error handler initialized")
    
    def classify_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorClassification:
        """
        Classify an error and suggest recovery strategy.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            ErrorClassification with suggested recovery
        """
        error_message = str(error)
        error_type = self._determine_error_type(error, error_message)
        severity = self._determine_severity(error_type, error_message)
        recovery_strategy = self._determine_recovery_strategy(error_type, severity)
        suggested_action = self._generate_suggested_action(error_type, recovery_strategy, error_message)
        
        classification = ErrorClassification(
            error_message=error_message,
            error_type=error_type,
            severity=severity,
            recovery_strategy=recovery_strategy,
            suggested_action=suggested_action
        )
        
        self.error_history.append(classification)
        self._update_error_patterns(error_type, error_message)
        
        logger.info(f"Error classified: {error_type.value} ({severity.value}) - {suggested_action}")
        
        return classification
    
    def _determine_error_type(self, error: Exception, error_message: str) -> ErrorType:
        """Determine the type of error."""
        error_name = type(error).__name__
        
        # API errors
        if "api" in error_message.lower() or "request" in error_message.lower():
            return ErrorType.LLM_API
        
        # Network errors
        if any(keyword in error_message.lower() for keyword in ["connection", "timeout", "network", "unreachable"]):
            return ErrorType.NETWORK
        
        # Timeout errors
        if "timeout" in error_message.lower() or error_name == "TimeoutError":
            return ErrorType.TIMEOUT
        
        # Permission errors
        if "permission" in error_message.lower() or error_name == "PermissionError":
            return ErrorType.PERMISSION
        
        # Resource errors
        if any(keyword in error_message.lower() for keyword in ["memory", "disk", "resource", "out of"]):
            return ErrorType.RESOURCE
        
        # Validation errors
        if "validation" in error_message.lower() or error_name == "ValueError":
            return ErrorType.VALIDATION
        
        # Tool execution errors
        if "tool" in error_message.lower() or error_name == "CalledProcessError":
            return ErrorType.TOOL_EXECUTION
        
        # Memory errors
        if "memory" in error_message.lower() or "chroma" in error_message.lower():
            return ErrorType.MEMORY
        
        return ErrorType.UNKNOWN
    
    def _determine_severity(self, error_type: ErrorType, error_message: str) -> ErrorSeverity:
        """Determine the severity of an error."""
        if error_type in [ErrorType.RESOURCE, ErrorType.PERMISSION]:
            return ErrorSeverity.CRITICAL
        
        if error_type in [ErrorType.LLM_API, ErrorType.MEMORY]:
            return ErrorSeverity.HIGH
        
        if error_type in [ErrorType.TIMEOUT, ErrorType.NETWORK]:
            return ErrorSeverity.MEDIUM
        
        if error_type in [ErrorType.VALIDATION, ErrorType.TOOL_EXECUTION]:
            if "critical" in error_message.lower():
                return ErrorSeverity.HIGH
            return ErrorSeverity.MEDIUM
        
        return ErrorSeverity.LOW
    
    def _determine_recovery_strategy(self, error_type: ErrorType, severity: ErrorSeverity) -> RecoveryStrategy:
        """Determine the best recovery strategy for an error."""
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.MANUAL_INTERVENTION
        
        if error_type == ErrorType.TIMEOUT:
            return RecoveryStrategy.RETRY
        
        if error_type == ErrorType.NETWORK:
            return RecoveryStrategy.RETRY
        
        if error_type == ErrorType.TOOL_EXECUTION:
            return RecoveryStrategy.FALLBACK_TOOL
        
        if error_type == ErrorType.VALIDATION:
            return RecoveryStrategy.ADJUST_PARAMS
        
        if error_type == ErrorType.LLM_API:
            return RecoveryStrategy.RETRY
        
        if error_type == ErrorType.MEMORY:
            return RecoveryStrategy.SKIP_STEP
        
        return RecoveryStrategy.ABORT
    
    def _generate_suggested_action(
        self,
        error_type: ErrorType,
        recovery_strategy: RecoveryStrategy,
        error_message: str
    ) -> str:
        """Generate a suggested action for recovery."""
        if recovery_strategy == RecoveryStrategy.RETRY:
            return f"Retry the operation (error: {error_type.value})"
        
        if recovery_strategy == RecoveryStrategy.FALLBACK_TOOL:
            return f"Try an alternative tool or approach"
        
        if recovery_strategy == RecoveryStrategy.ADJUST_PARAMS:
            return f"Adjust parameters and retry"
        
        if recovery_strategy == RecoveryStrategy.SKIP_STEP:
            return f"Skip this step and continue"
        
        if recovery_strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            return f"Manual intervention required: {error_message[:100]}"
        
        return f"Abort operation and report error"
    
    def _update_error_patterns(self, error_type: ErrorType, error_message: str):
        """Update error patterns for learning."""
        key = error_type.value
        
        if key not in self.error_patterns:
            self.error_patterns[key] = {
                "count": 0,
                "last_occurrence": None,
                "messages": []
            }
        
        self.error_patterns[key]["count"] += 1
        self.error_patterns[key]["last_occurrence"] = datetime.now().isoformat()
        
        # Store unique error messages (limit to 10)
        if error_message not in self.error_patterns[key]["messages"]:
            self.error_patterns[key]["messages"].append(error_message)
            if len(self.error_patterns[key]["messages"]) > 10:
                self.error_patterns[key]["messages"] = self.error_patterns[key]["messages"][-10:]
    
    def record_recovery_success(self, error_type: ErrorType, strategy: RecoveryStrategy, success: bool):
        """Record the success of a recovery strategy."""
        key = f"{error_type.value}_{strategy.value}"
        
        if key not in self.recovery_success_rate:
            self.recovery_success_rate[key] = {"success": 0, "total": 0}
        
        self.recovery_success_rate[key]["total"] += 1
        if success:
            self.recovery_success_rate[key]["success"] += 1
        
        success_rate = self.recovery_success_rate[key]["success"] / self.recovery_success_rate[key]["total"]
        logger.info(f"Recovery strategy {strategy.value} for {error_type.value}: {success_rate:.2%} success rate")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get statistics about errors and recovery."""
        total_errors = len(self.error_history)
        error_by_type = {}
        error_by_severity = {}
        
        for classification in self.error_history:
            error_type = classification.error_type.value
            severity = classification.severity.value
            
            error_by_type[error_type] = error_by_type.get(error_type, 0) + 1
            error_by_severity[severity] = error_by_severity.get(severity, 0) + 1
        
        return {
            "total_errors": total_errors,
            "error_by_type": error_by_type,
            "error_by_severity": error_by_severity,
            "error_patterns": self.error_patterns,
            "recovery_success_rate": self.recovery_success_rate
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors."""
        return [
            {
                "error_message": e.error_message,
                "error_type": e.error_type.value,
                "severity": e.severity.value,
                "recovery_strategy": e.recovery_strategy.value,
                "suggested_action": e.suggested_action,
                "timestamp": e.timestamp
            }
            for e in self.error_history[-limit:]
        ]

class SelfCorrectionEngine:
    """
    Self-correction engine that learns from errors and adjusts strategies.
    """
    
    def __init__(self, error_handler: ErrorHandler):
        """Initialize the self-correction engine."""
        self.error_handler = error_handler
        self.correction_history: List[Dict[str, Any]] = []
        logger.info("Self-correction engine initialized")
    
    async def attempt_correction(
        self,
        error: Exception,
        context: Dict[str, Any],
        retry_callback: callable
    ) -> tuple[bool, Optional[str]]:
        """
        Attempt to correct an error using recovery strategies.
        
        Args:
            error: The exception that occurred
            context: Context about the error
            retry_callback: Callback function to retry the operation
            
        Returns:
            Tuple of (success, result_or_error_message)
        """
        classification = self.error_handler.classify_error(error, context)
        
        logger.info(f"Attempting correction: {classification.recovery_strategy.value}")
        
        try:
            if classification.recovery_strategy == RecoveryStrategy.RETRY:
                result = await retry_callback()
                self.error_handler.record_recovery_success(
                    classification.error_type,
                    classification.recovery_strategy,
                    True
                )
                return True, result
            
            elif classification.recovery_strategy == RecoveryStrategy.ADJUST_PARAMS:
                # Adjust parameters (implementation depends on context)
                logger.info("Adjusting parameters for retry...")
                result = await retry_callback()
                self.error_handler.record_recovery_success(
                    classification.error_type,
                    classification.recovery_strategy,
                    True
                )
                return True, result
            
            elif classification.recovery_strategy == RecoveryStrategy.SKIP_STEP:
                logger.info("Skipping step and continuing...")
                self.error_handler.record_recovery_success(
                    classification.error_type,
                    classification.recovery_strategy,
                    True
                )
                return True, "Step skipped"
            
            else:
                self.error_handler.record_recovery_success(
                    classification.error_type,
                    classification.recovery_strategy,
                    False
                )
                return False, classification.suggested_action
        
        except Exception as e:
            logger.error(f"Correction attempt failed: {str(e)}")
            self.error_handler.record_recovery_success(
                classification.error_type,
                classification.recovery_strategy,
                False
            )
            return False, str(e)

# Global instances
_error_handler: Optional[ErrorHandler] = None
_self_correction_engine: Optional[SelfCorrectionEngine] = None

def get_error_handler() -> ErrorHandler:
    """Get or create the global error handler."""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def get_self_correction_engine() -> SelfCorrectionEngine:
    """Get or create the global self-correction engine."""
    global _self_correction_engine
    if _self_correction_engine is None:
        _self_correction_engine = SelfCorrectionEngine(get_error_handler())
    return _self_correction_engine
