"""
Production-grade monitoring and health check system.
Tracks metrics, health status, and performance indicators.
"""

import logging
import time
import psutil
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

@dataclass
class HealthCheckResult:
    """Result of a health check."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

@dataclass
class MetricPoint:
    """A single metric data point."""
    name: str
    value: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: Dict[str, str] = field(default_factory=dict)

class MetricsCollector:
    """Collects and tracks system and application metrics."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.metrics: Dict[str, List[MetricPoint]] = {}
        self.max_points_per_metric = 1000
        logger.info("Metrics collector initialized")
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric value."""
        if name not in self.metrics:
            self.metrics[name] = []
        
        point = MetricPoint(name=name, value=value, tags=tags or {})
        self.metrics[name].append(point)
        
        # Clean up old points
        if len(self.metrics[name]) > self.max_points_per_metric:
            self.metrics[name] = self.metrics[name][-self.max_points_per_metric:]
    
    def get_metric_stats(self, name: str, window_minutes: int = 60) -> Optional[Dict[str, float]]:
        """Get statistics for a metric over a time window."""
        if name not in self.metrics:
            return None
        
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_points = [
            p for p in self.metrics[name]
            if datetime.fromisoformat(p.timestamp) > cutoff_time
        ]
        
        if not recent_points:
            return None
        
        values = [p.value for p in recent_points]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1]
        }
    
    def get_all_metrics(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all recorded metrics."""
        return {
            name: [
                {
                    "value": p.value,
                    "timestamp": p.timestamp,
                    "tags": p.tags
                }
                for p in points[-100:]  # Return last 100 points
            ]
            for name, points in self.metrics.items()
        }

class HealthChecker:
    """Performs health checks on system and application components."""
    
    def __init__(self):
        """Initialize the health checker."""
        self.checks: Dict[str, callable] = {}
        self.last_check_results: Dict[str, HealthCheckResult] = {}
        self.metrics_collector = MetricsCollector()
        
        # Register default checks
        self._register_default_checks()
        logger.info("Health checker initialized")
    
    def _register_default_checks(self):
        """Register default health checks."""
        self.register_check("system_memory", self._check_system_memory)
        self.register_check("system_cpu", self._check_system_cpu)
        self.register_check("system_disk", self._check_system_disk)
        self.register_check("process_memory", self._check_process_memory)
        self.register_check("process_cpu", self._check_process_cpu)
    
    def register_check(self, name: str, check_func: callable):
        """Register a custom health check."""
        self.checks[name] = check_func
        logger.info(f"Registered health check: {name}")
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all registered health checks."""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                result = check_func()
                results[name] = result
                self.last_check_results[name] = result
            except Exception as e:
                result = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed: {str(e)}"
                )
                results[name] = result
                self.last_check_results[name] = result
        
        return results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall health status based on all checks."""
        if not self.last_check_results:
            return HealthStatus.HEALTHY
        
        statuses = [r.status for r in self.last_check_results.values()]
        
        if HealthStatus.CRITICAL in statuses:
            return HealthStatus.CRITICAL
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def _check_system_memory(self) -> HealthCheckResult:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            percent = memory.percent
            
            self.metrics_collector.record_metric("system_memory_percent", percent)
            
            if percent > 90:
                status = HealthStatus.CRITICAL
                message = f"System memory critical: {percent}%"
            elif percent > 75:
                status = HealthStatus.UNHEALTHY
                message = f"System memory high: {percent}%"
            elif percent > 60:
                status = HealthStatus.DEGRADED
                message = f"System memory elevated: {percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"System memory OK: {percent}%"
            
            return HealthCheckResult(
                name="system_memory",
                status=status,
                message=message,
                details={
                    "percent": percent,
                    "used": memory.used,
                    "available": memory.available,
                    "total": memory.total
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="system_memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check memory: {str(e)}"
            )
    
    def _check_system_cpu(self) -> HealthCheckResult:
        """Check system CPU usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            
            self.metrics_collector.record_metric("system_cpu_percent", cpu_percent)
            
            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                message = f"System CPU critical: {cpu_percent}%"
            elif cpu_percent > 75:
                status = HealthStatus.UNHEALTHY
                message = f"System CPU high: {cpu_percent}%"
            elif cpu_percent > 60:
                status = HealthStatus.DEGRADED
                message = f"System CPU elevated: {cpu_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"System CPU OK: {cpu_percent}%"
            
            return HealthCheckResult(
                name="system_cpu",
                status=status,
                message=message,
                details={
                    "percent": cpu_percent,
                    "cpu_count": psutil.cpu_count()
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="system_cpu",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check CPU: {str(e)}"
            )
    
    def _check_system_disk(self) -> HealthCheckResult:
        """Check system disk usage."""
        try:
            disk = psutil.disk_usage("/")
            percent = disk.percent
            
            self.metrics_collector.record_metric("system_disk_percent", percent)
            
            if percent > 90:
                status = HealthStatus.CRITICAL
                message = f"System disk critical: {percent}%"
            elif percent > 75:
                status = HealthStatus.UNHEALTHY
                message = f"System disk high: {percent}%"
            elif percent > 60:
                status = HealthStatus.DEGRADED
                message = f"System disk elevated: {percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"System disk OK: {percent}%"
            
            return HealthCheckResult(
                name="system_disk",
                status=status,
                message=message,
                details={
                    "percent": percent,
                    "used": disk.used,
                    "free": disk.free,
                    "total": disk.total
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="system_disk",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check disk: {str(e)}"
            )
    
    def _check_process_memory(self) -> HealthCheckResult:
        """Check process memory usage."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            self.metrics_collector.record_metric("process_memory_percent", memory_percent)
            
            if memory_percent > 50:
                status = HealthStatus.DEGRADED
                message = f"Process memory high: {memory_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Process memory OK: {memory_percent}%"
            
            return HealthCheckResult(
                name="process_memory",
                status=status,
                message=message,
                details={
                    "percent": memory_percent,
                    "rss": memory_info.rss,
                    "vms": memory_info.vms
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="process_memory",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check process memory: {str(e)}"
            )
    
    def _check_process_cpu(self) -> HealthCheckResult:
        """Check process CPU usage."""
        try:
            process = psutil.Process()
            cpu_percent = process.cpu_percent(interval=0.1)
            
            self.metrics_collector.record_metric("process_cpu_percent", cpu_percent)
            
            if cpu_percent > 50:
                status = HealthStatus.DEGRADED
                message = f"Process CPU high: {cpu_percent}%"
            else:
                status = HealthStatus.HEALTHY
                message = f"Process CPU OK: {cpu_percent}%"
            
            return HealthCheckResult(
                name="process_cpu",
                status=status,
                message=message,
                details={
                    "percent": cpu_percent
                }
            )
        except Exception as e:
            return HealthCheckResult(
                name="process_cpu",
                status=HealthStatus.UNHEALTHY,
                message=f"Failed to check process CPU: {str(e)}"
            )

class PerformanceMonitor:
    """Monitors performance metrics for operations."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize the performance monitor."""
        self.metrics_collector = metrics_collector
        self.operation_times: Dict[str, List[float]] = {}
        logger.info("Performance monitor initialized")
    
    def record_operation_time(self, operation_name: str, duration: float):
        """Record the duration of an operation."""
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []
        
        self.operation_times[operation_name].append(duration)
        
        # Keep only last 1000 measurements
        if len(self.operation_times[operation_name]) > 1000:
            self.operation_times[operation_name] = self.operation_times[operation_name][-1000:]
        
        self.metrics_collector.record_metric(f"operation_{operation_name}_time", duration)
    
    def get_operation_stats(self, operation_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for an operation."""
        if operation_name not in self.operation_times:
            return None
        
        times = self.operation_times[operation_name]
        
        return {
            "count": len(times),
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "latest": times[-1]
        }

# Global instances
_health_checker: Optional[HealthChecker] = None
_performance_monitor: Optional[PerformanceMonitor] = None

def get_health_checker() -> HealthChecker:
    """Get or create the global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the global performance monitor."""
    global _performance_monitor
    if _performance_monitor is None:
        health_checker = get_health_checker()
        _performance_monitor = PerformanceMonitor(health_checker.metrics_collector)
    return _performance_monitor


class MonitorFacade:
    """Unified monitoring facade combining health checker and metrics."""
    
    def __init__(self):
        self.health_checker = get_health_checker()
        self.performance_monitor = get_performance_monitor()
        self._metrics: Dict[str, float] = {}
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a metric value."""
        self._metrics[name] = self._metrics.get(name, 0) + value
        self.health_checker.metrics_collector.record_metric(name, value, tags)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all metrics."""
        return {
            "counters": self._metrics,
            "all_metrics": self.health_checker.metrics_collector.get_all_metrics(),
            "health_status": self.health_checker.get_overall_status()
        }

# Global monitor instance
_monitor: Optional[MonitorFacade] = None

def get_monitor() -> MonitorFacade:
    """Get or create the global monitor facade."""
    global _monitor
    if _monitor is None:
        _monitor = MonitorFacade()
    return _monitor
