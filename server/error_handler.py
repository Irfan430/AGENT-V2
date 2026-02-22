"""
Advanced error handling and self-correction system.
Classifies errors, suggests recovery strategies, and learns from failures.
Implements Phase 3.1 and 3.2 of the Production Roadmap.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum
import json
import asyncio

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
    PARSING = "parsing"
    UNKNOWN = "unknown"

class RecoveryStrategy(str, Enum):
    """Recovery strategies for different error types."""
    RETRY = "retry"
    FALLBACK_TOOL = "fallback_tool"
    ADJUST_PARAMS = "adjust_params"
    SKIP_STEP = "skip_step"
    ABORT = "abort"
    MANUAL_INTERVENTION = "manual_intervention"
    REFLECT_AND_REPLAN = "reflect_and_replan"

class ErrorClassification:
    """Classification of an error."""
    
    def __init__(
        self,
        error_message: str,
        error_type: ErrorType,
        severity: ErrorSeverity,
        recovery_strategy: RecoveryStrategy,
        suggested_action: str,
        context: Optional[Dict[str, Any]] = None
    ):
        self.error_message = error_message
        self.error_type = error_type
        self.severity = severity
        self.recovery_strategy = recovery_strategy
        self.suggested_action = suggested_action
        self.context = context or {}
        self.timestamp = datetime.now().isoformat()

class ErrorHandler:
    """
    Advanced error handling system with classification and recovery.
    """
    
    def __init__(self):
        """Initialize the error handler."""
        self.error_patterns: Dict[str, Dict[str, Any]] = {}
        self.error_history: List[ErrorClassification] = []
        self.recovery_success_rate: Dict[str, Dict[str, int]] = {}
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
        error_type = self._determine_error_type(error, error_message, context)
        severity = self._determine_severity(error_type, error_message)
        recovery_strategy = self._determine_recovery_strategy(error_type, severity)
        suggested_action = self._generate_suggested_action(error_type, recovery_strategy, error_message)
        
        classification = ErrorClassification(
            error_message=error_message,
            error_type=error_type,
            severity=severity,
            recovery_strategy=recovery_strategy,
            suggested_action=suggested_action,
            context=context
        )
        
        self.error_history.append(classification)
        self._update_error_patterns(error_type, error_message)
        
        logger.info(f"Error classified: {error_type.value} ({severity.value}) - {suggested_action}")
        
        return classification
    
    def _determine_error_type(self, error: Exception, error_message: str, context: Optional[Dict[str, Any]]) -> ErrorType:
        """Determine the type of error."""
        error_name = type(error).__name__
        
        # Specific checks based on common error messages/types
        if "api key" in error_message.lower() or "authentication" in error_message.lower() or "401" in error_message:
            return ErrorType.LLM_API
        if "connection refused" in error_message.lower() or "host unreachable" in error_message.lower():
            return ErrorType.NETWORK
        if "timeout" in error_message.lower() or error_name == "TimeoutError" or "asyncio.TimeoutError" in error_message:
            return ErrorType.TIMEOUT
        if "permission denied" in error_message.lower() or error_name == "PermissionError":
            return ErrorType.PERMISSION
        if "no space left" in error_message.lower() or "memory" in error_message.lower():
            return ErrorType.RESOURCE
        if "jsondecodeerror" in error_message.lower() or "failed to parse json" in error_message.lower():
            return ErrorType.PARSING
        if "validation error" in error_message.lower() or error_name == "ValueError":
            return ErrorType.VALIDATION
        
        # Context-based checks
        if context and "last_action" in context:
            action_type = context["last_action"].get("type")
            if action_type == "tool_call":
                return ErrorType.TOOL_EXECUTION
        
        if "chroma" in error_message.lower() or "vector database" in error_message.lower():
            return ErrorType.MEMORY
        
        return ErrorType.UNKNOWN
    
    def _determine_severity(self, error_type: ErrorType, error_message: str) -> ErrorSeverity:
        """Determine the severity of an error."""
        if error_type in [ErrorType.RESOURCE, ErrorType.PERMISSION, ErrorType.LLM_API]:
            return ErrorSeverity.CRITICAL
        
        if error_type in [ErrorType.MEMORY, ErrorType.NETWORK, ErrorType.TIMEOUT]:
            return ErrorSeverity.HIGH
        
        if error_type in [ErrorType.TOOL_EXECUTION, ErrorType.PARSING]:
            return ErrorSeverity.MEDIUM
        
        if error_type == ErrorType.VALIDATION:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.UNKNOWN
    
    def _determine_recovery_strategy(self, error_type: ErrorType, severity: ErrorSeverity) -> RecoveryStrategy:
        """Determine the best recovery strategy for an error."""
        if severity == ErrorSeverity.CRITICAL:
            return RecoveryStrategy.REFLECT_AND_REPLAN # Agent needs to rethink fundamentally
        
        if error_type in [ErrorType.TIMEOUT, ErrorType.NETWORK, ErrorType.LLM_API]:
            return RecoveryStrategy.RETRY
        
        if error_type == ErrorType.TOOL_EXECUTION:
            return RecoveryStrategy.FALLBACK_TOOL
        
        if error_type == ErrorType.VALIDATION:
            return RecoveryStrategy.ADJUST_PARAMS
        
        if error_type == ErrorType.PARSING:
            return RecoveryStrategy.REFLECT_AND_REPLAN # Agent needs to adjust its output format
        
        if error_type == ErrorType.MEMORY:
            return RecoveryStrategy.REFLECT_AND_REPLAN # Memory issues often require re-evaluation
        
        return RecoveryStrategy.ABORT
    
    def _generate_suggested_action(
        self,
        error_type: ErrorType,
        recovery_strategy: RecoveryStrategy,
        error_message: str
    ) -> str:
        """Generate a suggested action for recovery."""
        if recovery_strategy == RecoveryStrategy.RETRY:
            return f"Retry the last operation (error: {error_type.value})"
        
        if recovery_strategy == RecoveryStrategy.FALLBACK_TOOL:
            return f"Try an alternative tool or approach for the current step"
        
        if recovery_strategy == RecoveryStrategy.ADJUST_PARAMS:
            return f"Adjust parameters for the tool call and retry"
        
        if recovery_strategy == RecoveryStrategy.SKIP_STEP:
            return f"Skip this problematic step and attempt to continue with the plan"
        
        if recovery_strategy == RecoveryStrategy.REFLECT_AND_REPLAN:
            return f"Reflect on the error and generate a new plan to overcome it"
        
        if recovery_strategy == RecoveryStrategy.MANUAL_INTERVENTION:
            return f"Manual intervention required: {error_message[:100]}..."
        
        return f"Abort operation and report error: {error_message[:100]}..."
    
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
        
        if error_message not in self.error_patterns[key]["messages"]:
            self.error_patterns[key]["messages"].append(error_message)
            if len(self.error_patterns[key]["messages"]) > 10:
                self.error_patterns[key]["messages"] = self.error_patterns[key]["messages"][-10:]
    
    def record_recovery_attempt(self, error_type: ErrorType, strategy: RecoveryStrategy, success: bool):
        """Record the success of a recovery strategy."""
        key = f"{error_type.value}_{strategy.value}"
        
        if key not in self.recovery_success_rate:
            self.recovery_success_rate[key] = {"success": 0, "total": 0}
        
        self.recovery_success_rate[key]["total"] += 1
        if success:
            self.recovery_success_rate[key]["success"] += 1
        
        success_count = self.recovery_success_rate[key]["success"]
        total_count = self.recovery_success_rate[key]["total"]
        logger.info(f"Recovery strategy {strategy.value} for {error_type.value}: {success_count}/{total_count} success")
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about errors and recovery."""
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
    Implements Phase 3.2 of the Production Roadmap.
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
        llm_client: Any, # Pass LLM client here to avoid circular dependency
        system_prompt: str,
        available_tools: List[Dict[str, Any]]
    ) -> tuple[bool, Optional[str]]:
        """
        Attempt to correct an error using recovery strategies.
        
        Args:
            error: The exception that occurred
            context: Additional context about the error (e.g., last action, user message)
            llm_client: The LLM client instance for generating new thoughts/plans
            system_prompt: The system prompt for the LLM
            available_tools: List of available tools for the LLM to consider
            
        Returns:
            A tuple (correction_attempted, correction_message).
        """
        classification = self.error_handler.classify_error(error, context)
        strategy = classification.recovery_strategy
        error_message = classification.error_message
        
        logger.info(f"Attempting self-correction with strategy: {strategy.value}")
        
        correction_message = None
        correction_success = False
        
        if strategy == RecoveryStrategy.RETRY:
            # Simple retry logic (handled by orchestrator for now, but could be here)
            correction_message = f"Retrying operation due to {classification.error_type.value} error."
            correction_success = True # Assume retry is an attempt
            
        elif strategy == RecoveryStrategy.REFLECT_AND_REPLAN:
            # Use LLM to reflect and generate a new plan
            reflection_prompt = f"""An error occurred during agent execution. Reflect on the error and propose a new plan or action.

Error Type: {classification.error_type.value}
Error Message: {error_message}
Context: {json.dumps(context, indent=2)}

Based on this, what is the best next step? Provide your response in JSON format:
{{
  "reasoning": "Your detailed reasoning for the new plan/action",
  "plan": ["Step 1", "Step 2", ...],
  "next_action": "The name of the tool to call, or 'respond' to give the final answer",
  "tool_input": {{ "param1": "value1", ... }},
  "confidence": 0.8
}}
"""
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": reflection_prompt}
            ]
            
            try:
                response = await llm_client.chat_completion_async(messages=messages, temperature=0.5, max_tokens=1024)
                response_content = response.content.strip()
                if response_content.startswith("```json"):
                    response_content = response_content[7:-3].strip()
                elif response_content.startswith("```"):
                    response_content = response_content[3:-3].strip()
                
                reflection_data = json.loads(response_content)
                reasoning = reflection_data.get("reasoning", "No specific reasoning provided.")
                correction_message = f"Agent reflected and proposed new plan: {reasoning}"
                correction_success = True
                # The orchestrator will use this new thought to update its state
                context["new_thought_from_reflection"] = reflection_data
                
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse reflection response: {str(e)}. Raw: {response_content}")
                correction_message = f"Reflection failed due to parsing error: {str(e)}"
                correction_success = False
            
        # Other strategies like FALLBACK_TOOL, ADJUST_PARAMS would require more complex logic
        # For now, we'll focus on RETRY and REFLECT_AND_REPLAN
        
        self.error_handler.record_recovery_attempt(classification.error_type, strategy, correction_success)
        self.correction_history.append({
            "timestamp": datetime.now().isoformat(),
            "error_classification": classification.__dict__,
            "strategy_attempted": strategy.value,
            "success": correction_success,
            "message": correction_message
        })
        
        return correction_success, correction_message

# Global instance
_error_handler = None
_self_correction_engine = None

def get_error_handler() -> ErrorHandler:
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def get_self_correction_engine() -> SelfCorrectionEngine:
    global _self_correction_engine
    if _self_correction_engine is None:
        _self_correction_engine = SelfCorrectionEngine(get_error_handler())
    return _self_correction_engine
