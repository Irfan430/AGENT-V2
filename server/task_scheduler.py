"""
Task scheduling and automation system using APScheduler.
Supports recurring tasks, one-time tasks, and parallel execution.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime, timedelta
from enum import Enum
import json

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    APSCHEDULER_AVAILABLE = True
except ImportError:
    APSCHEDULER_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("APScheduler not installed. Install with: pip install apscheduler")

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskScheduler:
    """
    Task scheduling and automation system.
    Manages recurring tasks, one-time tasks, and parallel execution.
    """
    
    def __init__(self):
        """Initialize the task scheduler."""
        if not APSCHEDULER_AVAILABLE:
            logger.error("APScheduler not available")
            self.scheduler = None
            self.tasks = {}
            return
        
        self.scheduler = AsyncIOScheduler()
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        logger.info("Task scheduler initialized")
    
    async def start(self):
        """Start the scheduler."""
        if not self.scheduler:
            logger.error("Scheduler not available")
            return
        
        try:
            self.scheduler.start()
            logger.info("Task scheduler started")
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
    
    async def stop(self):
        """Stop the scheduler."""
        if not self.scheduler:
            return
        
        try:
            self.scheduler.shutdown()
            logger.info("Task scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    async def schedule_once(self, task_id: str, task_name: str,
                           task_func: Callable, run_at: datetime,
                           kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule a one-time task.
        
        Args:
            task_id: Unique task ID
            task_name: Human-readable task name
            task_func: Async function to execute
            run_at: When to run the task
            kwargs: Arguments to pass to task function
            
        Returns:
            Task scheduling result
        """
        if not self.scheduler:
            return {
                "success": False,
                "error": "Scheduler not available"
            }
        
        try:
            kwargs = kwargs or {}
            
            # Schedule the task
            job = self.scheduler.add_job(
                task_func,
                trigger='date',
                run_date=run_at,
                args=[],
                kwargs=kwargs,
                id=task_id,
                name=task_name,
                replace_existing=True
            )
            
            # Record task
            self.tasks[task_id] = {
                "id": task_id,
                "name": task_name,
                "type": "one-time",
                "status": TaskStatus.PENDING,
                "scheduled_at": datetime.now().isoformat(),
                "run_at": run_at.isoformat(),
                "kwargs": kwargs
            }
            
            logger.info(f"Scheduled one-time task: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "task_name": task_name,
                "type": "one-time",
                "scheduled_at": datetime.now().isoformat(),
                "run_at": run_at.isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scheduling task: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def schedule_recurring(self, task_id: str, task_name: str,
                                task_func: Callable, cron_expression: str,
                                kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule a recurring task with cron expression.
        
        Args:
            task_id: Unique task ID
            task_name: Human-readable task name
            task_func: Async function to execute
            cron_expression: Cron expression (e.g., '0 9 * * *' for daily at 9am)
            kwargs: Arguments to pass to task function
            
        Returns:
            Task scheduling result
        """
        if not self.scheduler:
            return {
                "success": False,
                "error": "Scheduler not available"
            }
        
        try:
            kwargs = kwargs or {}
            
            # Schedule the recurring task
            job = self.scheduler.add_job(
                task_func,
                trigger=CronTrigger.from_crontab(cron_expression),
                args=[],
                kwargs=kwargs,
                id=task_id,
                name=task_name,
                replace_existing=True
            )
            
            # Record task
            self.tasks[task_id] = {
                "id": task_id,
                "name": task_name,
                "type": "recurring",
                "status": TaskStatus.PENDING,
                "scheduled_at": datetime.now().isoformat(),
                "cron_expression": cron_expression,
                "kwargs": kwargs
            }
            
            logger.info(f"Scheduled recurring task: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "task_name": task_name,
                "type": "recurring",
                "cron_expression": cron_expression,
                "scheduled_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scheduling recurring task: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def schedule_interval(self, task_id: str, task_name: str,
                               task_func: Callable, interval_seconds: int,
                               kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule a task to run at fixed intervals.
        
        Args:
            task_id: Unique task ID
            task_name: Human-readable task name
            task_func: Async function to execute
            interval_seconds: Interval in seconds
            kwargs: Arguments to pass to task function
            
        Returns:
            Task scheduling result
        """
        if not self.scheduler:
            return {
                "success": False,
                "error": "Scheduler not available"
            }
        
        try:
            kwargs = kwargs or {}
            
            # Schedule the interval task
            job = self.scheduler.add_job(
                task_func,
                trigger=IntervalTrigger(seconds=interval_seconds),
                args=[],
                kwargs=kwargs,
                id=task_id,
                name=task_name,
                replace_existing=True
            )
            
            # Record task
            self.tasks[task_id] = {
                "id": task_id,
                "name": task_name,
                "type": "interval",
                "status": TaskStatus.PENDING,
                "scheduled_at": datetime.now().isoformat(),
                "interval_seconds": interval_seconds,
                "kwargs": kwargs
            }
            
            logger.info(f"Scheduled interval task: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "task_name": task_name,
                "type": "interval",
                "interval_seconds": interval_seconds,
                "scheduled_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error scheduling interval task: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            Cancellation result
        """
        if not self.scheduler:
            return {
                "success": False,
                "error": "Scheduler not available"
            }
        
        try:
            self.scheduler.remove_job(task_id)
            
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = TaskStatus.CANCELLED
            
            logger.info(f"Cancelled task: {task_id}")
            
            return {
                "success": True,
                "task_id": task_id,
                "status": "cancelled"
            }
        
        except Exception as e:
            logger.error(f"Error cancelling task: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task."""
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get all scheduled tasks."""
        return self.tasks.copy()
    
    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get task execution history."""
        return self.task_history[-limit:]
    
    async def record_task_execution(self, task_id: str, 
                                   success: bool, result: Any = None,
                                   error: Optional[str] = None):
        """Record task execution in history."""
        execution_record = {
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "result": result,
            "error": error
        }
        
        self.task_history.append(execution_record)
        
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            self.tasks[task_id]["last_execution"] = execution_record

# Global task scheduler instance
_task_scheduler: Optional[TaskScheduler] = None

def get_task_scheduler() -> TaskScheduler:
    """Get or create the global task scheduler."""
    global _task_scheduler
    if _task_scheduler is None:
        _task_scheduler = TaskScheduler()
    return _task_scheduler
