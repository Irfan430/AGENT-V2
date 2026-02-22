"""
Production-grade Task scheduling and automation system using APScheduler.
Supports recurring tasks, one-time tasks, and parallel execution.
Implements Phase 5 of the Production Roadmap.
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
    print("WARNING: APScheduler not installed. Task scheduling features will be disabled. Install with: pip install apscheduler")

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
    Production-grade task scheduling and automation system.
    Manages recurring tasks, one-time tasks, and parallel execution.
    """
    
    def __init__(self):
        """Initialize the task scheduler."""
        if not APSCHEDULER_AVAILABLE:
            logger.error("APScheduler not available. Task scheduling disabled.")
            self.scheduler = None
            self.tasks = {}
            self.task_history = []
            return
        
        self.scheduler = AsyncIOScheduler()
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.task_history: List[Dict[str, Any]] = []
        logger.info("Production Task scheduler initialized")
    
    async def start(self):
        """Start the scheduler."""
        if not self.scheduler:
            logger.warning("Scheduler not available, cannot start.")
            return
        
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Task scheduler started")
            else:
                logger.info("Task scheduler already running.")
        except Exception as e:
            logger.error(f"Error starting scheduler: {str(e)}")
    
    async def stop(self):
        """Stop the scheduler."""
        if not self.scheduler:
            return
        
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Task scheduler stopped")
            else:
                logger.info("Task scheduler not running.")
        except Exception as e:
            logger.error(f"Error stopping scheduler: {str(e)}")
    
    async def _task_wrapper(self, task_id: str, task_func_name: str, task_func_kwargs: Dict[str, Any]):
        """
        Wrapper to execute task function via ToolManager and record its status.
        """
        from server.tool_manager import get_tool_manager # Import here to avoid circular dependency
        tool_manager = get_tool_manager()

        logger.info(f"Executing scheduled task: {task_id} - {task_func_name}")
        self.tasks[task_id]["status"] = TaskStatus.RUNNING
        self.tasks[task_id]["last_run_time"] = datetime.now().isoformat()
        
        success = False
        result = None
        error_msg = None
        try:
            tool_result = await tool_manager.execute_tool(task_func_name, task_func_kwargs)
            success = tool_result.get("success", False)
            if success:
                result = tool_result.get("result")
                logger.info(f"Task {task_id} completed successfully.")
            else:
                error_msg = tool_result.get("error", "Unknown error during tool execution")
                logger.error(f"Task {task_id} failed: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Task {task_id} failed with exception: {error_msg}")
        finally:
            await self.record_task_execution(task_id, success, result, error_msg)
            if task_id in self.tasks and self.tasks[task_id]["type"] == "one-time":
                del self.tasks[task_id] # Remove one-time tasks after execution

    async def schedule_once(self, task_id: str, task_name: str,
                           run_at: datetime, task_func_name: str,
                           task_func_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule a one-time task.
        """
        if not self.scheduler:
            return {"success": False, "error": "Scheduler not available"}
        
        try:
            task_func_kwargs = task_func_kwargs or {}
            
            self.scheduler.add_job(
                self._task_wrapper,
                trigger='date',
                run_date=run_at,
                args=[task_id, task_func_name, task_func_kwargs],
                id=task_id,
                name=task_name,
                replace_existing=True
            )
            
            self.tasks[task_id] = {
                "id": task_id,
                "name": task_name,
                "type": "one-time",
                "status": TaskStatus.PENDING,
                "scheduled_at": datetime.now().isoformat(),
                "run_at": run_at.isoformat(),
                "task_func_name": task_func_name,
                "task_func_kwargs": task_func_kwargs
            }
            
            logger.info(f"Scheduled one-time task: {task_id} to run at {run_at}")
            return {"success": True, "task_id": task_id, "task_name": task_name, "type": "one-time", "scheduled_at": datetime.now().isoformat(), "run_at": run_at.isoformat()}
        
        except Exception as e:
            logger.error(f"Error scheduling one-time task {task_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def schedule_recurring(self, task_id: str, task_name: str,
                                task_func_name: str, cron_expression: str,
                                task_func_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule a recurring task with cron expression.
        """
        if not self.scheduler:
            return {"success": False, "error": "Scheduler not available"}
        
        try:
            task_func_kwargs = task_func_kwargs or {}
            
            self.scheduler.add_job(
                self._task_wrapper,
                trigger=CronTrigger.from_crontab(cron_expression),
                args=[task_id, task_func_name, task_func_kwargs],
                id=task_id,
                name=task_name,
                replace_existing=True
            )
            
            self.tasks[task_id] = {
                "id": task_id,
                "name": task_name,
                "type": "recurring",
                "status": TaskStatus.PENDING,
                "scheduled_at": datetime.now().isoformat(),
                "cron_expression": cron_expression,
                "task_func_name": task_func_name,
                "task_func_kwargs": task_func_kwargs
            }
            
            logger.info(f"Scheduled recurring task: {task_id} with cron: {cron_expression}")
            return {"success": True, "task_id": task_id, "task_name": task_name, "type": "recurring", "cron_expression": cron_expression, "scheduled_at": datetime.now().isoformat()}
        
        except Exception as e:
            logger.error(f"Error scheduling recurring task {task_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def schedule_interval(self, task_id: str, task_name: str,
                               task_func_name: str, interval_seconds: int,
                               task_func_kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Schedule a task to run at fixed intervals.
        """
        if not self.scheduler:
            return {"success": False, "error": "Scheduler not available"}
        
        try:
            task_func_kwargs = task_func_kwargs or {}
            
            self.scheduler.add_job(
                self._task_wrapper,
                trigger=IntervalTrigger(seconds=interval_seconds),
                args=[task_id, task_func_name, task_func_kwargs],
                id=task_id,
                name=task_name,
                replace_existing=True
            )
            
            self.tasks[task_id] = {
                "id": task_id,
                "name": task_name,
                "type": "interval",
                "status": TaskStatus.PENDING,
                "scheduled_at": datetime.now().isoformat(),
                "interval_seconds": interval_seconds,
                "task_func_name": task_func_name,
                "task_func_kwargs": task_func_kwargs
            }
            
            logger.info(f"Scheduled interval task: {task_id} every {interval_seconds} seconds")
            return {"success": True, "task_id": task_id, "task_name": task_name, "type": "interval", "interval_seconds": interval_seconds, "scheduled_at": datetime.now().isoformat()}
        
        except Exception as e:
            logger.error(f"Error scheduling interval task {task_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled task.
        """
        if not self.scheduler:
            return {"success": False, "error": "Scheduler not available"}
        
        try:
            self.scheduler.remove_job(task_id)
            if task_id in self.tasks:
                self.tasks[task_id]["status"] = TaskStatus.CANCELLED
            logger.info(f"Cancelled task: {task_id}")
            return {"success": True, "task_id": task_id, "status": "cancelled"}
        
        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a task.
        """
        return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all scheduled tasks.
        """
        return self.tasks.copy()
    
    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get task execution history.
        """
        return self.task_history[-limit:]
    
    async def record_task_execution(self, task_id: str, 
                                   success: bool, result: Any = None,
                                   error: Optional[str] = None):
        """
        Record task execution in history.
        """
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

async def initialize_task_scheduler():
    """Initialize and start the task scheduler."""
    scheduler = get_task_scheduler()
    await scheduler.start()
    return scheduler

async def shutdown_task_scheduler():
    """Shutdown the task scheduler."""
    scheduler = get_task_scheduler()
    await scheduler.stop()
