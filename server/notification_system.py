"""
Notification system for critical events and owner alerts.
Sends notifications for task completion, errors, and approval requests.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    """Types of notifications."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    APPROVAL_REQUIRED = "approval_required"

class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Notification:
    """Represents a single notification."""
    
    def __init__(self, title: str, content: str,
                 notification_type: NotificationType = NotificationType.INFO,
                 priority: NotificationPriority = NotificationPriority.MEDIUM,
                 data: Optional[Dict[str, Any]] = None):
        """
        Initialize a notification.
        
        Args:
            title: Notification title
            content: Notification content
            notification_type: Type of notification
            priority: Priority level
            data: Additional data
        """
        self.id = f"notif_{datetime.now().timestamp()}"
        self.title = title
        self.content = content
        self.type = notification_type
        self.priority = priority
        self.data = data or {}
        self.created_at = datetime.now().isoformat()
        self.read = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert notification to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "type": self.type.value,
            "priority": self.priority.value,
            "data": self.data,
            "created_at": self.created_at,
            "read": self.read
        }

class NotificationSystem:
    """
    Notification system for agent events.
    Manages notifications and sends alerts to the owner.
    """
    
    def __init__(self):
        """Initialize the notification system."""
        self.notifications: List[Notification] = []
        self.subscribers: List[callable] = []
        self.approval_requests: Dict[str, Dict[str, Any]] = {}
        logger.info("Notification system initialized")
    
    def subscribe(self, callback: callable):
        """
        Subscribe to notifications.
        
        Args:
            callback: Callback function to call on new notifications
        """
        self.subscribers.append(callback)
        logger.info("New subscriber registered")
    
    def notify(self, title: str, content: str,
              notification_type: NotificationType = NotificationType.INFO,
              priority: NotificationPriority = NotificationPriority.MEDIUM,
              data: Optional[Dict[str, Any]] = None) -> Notification:
        """
        Send a notification.
        
        Args:
            title: Notification title
            content: Notification content
            notification_type: Type of notification
            priority: Priority level
            data: Additional data
            
        Returns:
            Created notification
        """
        notification = Notification(
            title=title,
            content=content,
            notification_type=notification_type,
            priority=priority,
            data=data
        )
        
        self.notifications.append(notification)
        
        # Call subscribers
        for subscriber in self.subscribers:
            try:
                subscriber(notification)
            except Exception as e:
                logger.error(f"Error calling subscriber: {str(e)}")
        
        # Log based on priority
        if priority == NotificationPriority.CRITICAL:
            logger.critical(f"{title}: {content}")
        elif priority == NotificationPriority.HIGH:
            logger.error(f"{title}: {content}")
        else:
            logger.info(f"{title}: {content}")
        
        return notification
    
    def notify_task_completion(self, task_id: str, task_name: str,
                              success: bool, result: Any = None,
                              error: Optional[str] = None):
        """
        Notify about task completion.
        
        Args:
            task_id: Task ID
            task_name: Task name
            success: Whether task succeeded
            result: Task result
            error: Error message if failed
        """
        if success:
            self.notify(
                title=f"Task Completed: {task_name}",
                content=f"Task {task_id} completed successfully",
                notification_type=NotificationType.SUCCESS,
                priority=NotificationPriority.MEDIUM,
                data={
                    "task_id": task_id,
                    "task_name": task_name,
                    "result": str(result)[:200]
                }
            )
        else:
            self.notify(
                title=f"Task Failed: {task_name}",
                content=f"Task {task_id} failed: {error}",
                notification_type=NotificationType.ERROR,
                priority=NotificationPriority.HIGH,
                data={
                    "task_id": task_id,
                    "task_name": task_name,
                    "error": error
                }
            )
    
    def notify_error(self, error_title: str, error_message: str,
                    error_type: str = "unknown",
                    context: Optional[Dict[str, Any]] = None):
        """
        Notify about an error.
        
        Args:
            error_title: Error title
            error_message: Error message
            error_type: Type of error
            context: Additional context
        """
        self.notify(
            title=f"Error: {error_title}",
            content=error_message,
            notification_type=NotificationType.ERROR,
            priority=NotificationPriority.HIGH,
            data={
                "error_type": error_type,
                "context": context or {}
            }
        )
    
    def request_approval(self, request_id: str, title: str, description: str,
                        action: str, data: Optional[Dict[str, Any]] = None) -> str:
        """
        Request approval for a high-risk operation.
        
        Args:
            request_id: Unique request ID
            title: Approval request title
            description: Detailed description
            action: Action to be performed
            data: Additional data
            
        Returns:
            Request ID
        """
        approval_request = {
            "id": request_id,
            "title": title,
            "description": description,
            "action": action,
            "data": data or {},
            "created_at": datetime.now().isoformat(),
            "status": "pending",
            "approved_at": None
        }
        
        self.approval_requests[request_id] = approval_request
        
        self.notify(
            title=f"Approval Required: {title}",
            content=description,
            notification_type=NotificationType.APPROVAL_REQUIRED,
            priority=NotificationPriority.CRITICAL,
            data={
                "request_id": request_id,
                "action": action
            }
        )
        
        logger.warning(f"Approval requested: {request_id}")
        
        return request_id
    
    def approve_request(self, request_id: str) -> bool:
        """
        Approve a pending request.
        
        Args:
            request_id: Request ID
            
        Returns:
            Success status
        """
        if request_id not in self.approval_requests:
            return False
        
        self.approval_requests[request_id]["status"] = "approved"
        self.approval_requests[request_id]["approved_at"] = datetime.now().isoformat()
        
        logger.info(f"Request approved: {request_id}")
        
        return True
    
    def reject_request(self, request_id: str) -> bool:
        """
        Reject a pending request.
        
        Args:
            request_id: Request ID
            
        Returns:
            Success status
        """
        if request_id not in self.approval_requests:
            return False
        
        self.approval_requests[request_id]["status"] = "rejected"
        self.approval_requests[request_id]["approved_at"] = datetime.now().isoformat()
        
        logger.info(f"Request rejected: {request_id}")
        
        return True
    
    def get_approval_status(self, request_id: str) -> Optional[str]:
        """Get approval request status."""
        if request_id not in self.approval_requests:
            return None
        return self.approval_requests[request_id]["status"]
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests."""
        return [
            req for req in self.approval_requests.values()
            if req["status"] == "pending"
        ]
    
    def get_notifications(self, limit: int = 50,
                         unread_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get notifications.
        
        Args:
            limit: Maximum number of notifications
            unread_only: Only return unread notifications
            
        Returns:
            List of notifications
        """
        notifications = self.notifications[-limit:]
        
        if unread_only:
            notifications = [n for n in notifications if not n.read]
        
        return [n.to_dict() for n in notifications]
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read."""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.read = True
                return True
        return False
    
    def clear_old_notifications(self, days: int = 7) -> int:
        """
        Clear notifications older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of cleared notifications
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        initial_count = len(self.notifications)
        
        self.notifications = [
            n for n in self.notifications
            if datetime.fromisoformat(n.created_at) > cutoff_date
        ]
        
        cleared = initial_count - len(self.notifications)
        logger.info(f"Cleared {cleared} old notifications")
        
        return cleared

# Global notification system instance
_notification_system: Optional[NotificationSystem] = None

def get_notification_system() -> NotificationSystem:
    """Get or create the global notification system."""
    global _notification_system
    if _notification_system is None:
        _notification_system = NotificationSystem()
    return _notification_system
