"""Scheduler Engine - 调度引擎 + 高级调度系统"""
import asyncio
import logging
import threading
import time
from typing import Dict, List, Callable, Any, Union, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from queue import PriorityQueue
import heapq
import uuid
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    IDLE = 1

class ScheduledTask:
    """计划任务"""
    id: str
    name: str
    func: Callable
    interval_seconds: int
    priority: TaskPriority
    max_retries: int
    retry_delay: int
    timeout: Optional[int]
    dependencies: List[str]
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    state: TaskState = TaskState.PENDING
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __init__(
        self,
        task_id: str,
        name: str,
        func: Callable,
        interval_seconds: int = 3600,
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = 3,
        retry_delay: int = 5,
        timeout: Optional[int] = None,
        dependencies: Optional[List[str]] = None
    ):
        self.id = task_id
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.priority = priority
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.dependencies = dependencies or []
        self.next_run = datetime.now() + timedelta(seconds=interval_seconds)

class TaskEvent:
    """任务事件回调"""
    def __init__(self, task_id: str, event_type: str, data: Any = None):
        self.task_id = task_id
        self.event_type = event_type
        self.data = data
        self.timestamp = datetime.now()

class TaskEventCallback:
    """任务事件回调处理器"""
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {
            'on_start': [],
            'on_success': [],
            'on_failure': [],
            'on_retry': [],
            'on_cancel': [],
            'on_complete': []
        }
    
    def register(self, event_type: str, callback: Callable):
        """注册事件回调"""
        if event_type in self.listeners:
            self.listeners[event_type].append(callback)
    
    def unregister(self, event_type: str, callback: Callable):
        """注销事件回调"""
        if event_type in self.listeners and callback in self.listeners[event_type]:
            self.listeners[event_type].remove(callback)
    
    async def emit(self, event_type: str, event: TaskEvent):
        """触发事件回调"""
        if event_type in self.listeners:
            for callback in self.listeners[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event callback {event_type}: {e}")

class CronParser:
    """Cron表达式解析器"""
    CRON_FIELDS = ['minute', 'hour', 'day', 'month', 'weekday']
    
    def __init__(self, expression: str):
        self.expression = expression
        self.fields = expression.split()
        if len(self.fields) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
    
    def get_next_run(self, base_time: datetime = None) -> datetime:
        """计算下次执行时间"""
        if base_time is None:
            base_time = datetime.now()
        
        # 简化的cron解析实现
        minute, hour, day, month, weekday = self.fields
        
        next_time = base_time + timedelta(minutes=1)
        
        # 解析各字段并计算下次执行时间
        if minute != '*':
            next_time = self._parse_field(next_time, minute, 0, 59)
        
        return next_time
    
    def _parse_field(self, base_time: datetime, field: str, min_val: int, max_val: int) -> datetime:
        """解析单个cron字段"""
        if field == '*':
            return base_time
        
        # 处理列表
        if ',' in field:
            values = [int(v) for v in field.split(',')]
            for val in values:
                if min_val <= val <= max_val and base_time.minute <= val:
                    return base_time.replace(minute=val)
        
        # 处理范围
        if '-' in field:
            start, end = field.split('-')
            start_val, end_val = int(start), int(end)
            for val in range(start_val, end_val + 1):
                if min_val <= val <= max_val and base_time.minute <= val:
                    return base_time.replace(minute=val)
        
        # 处理步进
        if '/' in field:
            base, step = field.split('/')
            step_val = int(step)
            current = int(base) if base != '*' else min_val
            for val in range(current, max_val + 1, step_val):
                if base_time.minute <= val:
                    return base_time.replace(minute=val)
        
        # 处理单一值
        try:
            val = int(field)
            if min_val <= val <= max_val:
                return base_time.replace(minute=val)
        except ValueError:
            pass
        
        return base_time + timedelta(hours=1)

class DistributedLock:
    """分布式锁（简化实现）"""
    def __init__(self, lock_name: str):
        self.lock_name = lock_name
        self._lock = threading.Lock()
        self._held = False
    
    def acquire(self, timeout: float = 10.0) -> bool:
        """获取锁"""
        acquired = self._lock.acquire(timeout=timeout)
        if acquired:
            self._held = True
            logger.debug(f"Lock acquired: {self.lock_name}")
        return acquired
    
    def release(self):
        """释放锁"""
        if self._held:
            self._lock.release()
            self._held = False
            logger.debug(f"Lock released: {self.lock_name}")
    
    def __enter__(self):
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()

class TaskStatistics:
    """任务执行统计"""
    def __init__(self):
        self.total_executed: int = 0
        self.total_success: int = 0
        self.total_failed: int = 0
        self.total_retries: int = 0
        self.execution_times: Dict[str, List[float]] = {}
    
    def record_execution(self, task_id: str, duration: float, success: bool):
        """记录任务执行"""
        self.total_executed += 1
        if success:
            self.total_success += 1
        else:
            self.total_failed += 1
        
        if task_id not in self.execution_times:
            self.execution_times[task_id] = []
        self.execution_times[task_id].append(duration)
    
    def record_retry(self):
        """记录重试"""
        self.total_retries += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_executed': self.total_executed,
            'total_success': self.total_success,
            'total_failed': self.total_failed,
            'total_retries': self.total_retries,
            'success_rate': self.total_success / self.total_executed if self.total_executed > 0 else 0,
            'avg_execution_time': {
                task_id: sum(times) / len(times) if times else 0
                for task_id, times in self.execution_times.items()
            }
        }

class AdvancedScheduler:
    """高级调度器 - 支持Cron、重试、依赖、优先级、分布式锁"""
    
    def __init__(self, enable_distributed_lock: bool = False):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[tuple] = []  # (next_run_time, priority, task_id)
        self.running = False
        self.enable_distributed_lock = enable_distributed_lock
        self.locks: Dict[str, DistributedLock] = {}
        self.event_callback = TaskEventCallback()
        self.statistics = TaskStatistics()
        self._lock = threading.Lock()
        self.cancelled_tasks: set = set()
    
    def schedule(
        self,
        task_id: str,
        name: str,
        func: Callable,
        interval_seconds: int = 3600,
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = 3,
        retry_delay: int = 5,
        timeout: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        cron_expression: Optional[str] = None
    ):
        """调度任务"""
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            dependencies=dependencies
        )
        
        # 如果有cron表达式，解析下次执行时间
        if cron_expression:
            parser = CronParser(cron_expression)
            task.next_run = parser.get_next_run()
        
        self.tasks[task_id] = task
        
        # 优先级队列: (next_run_time, priority_value负数实现反向优先级, task_id)
        heapq.heappush(
            self.task_queue,
            (task.next_run, -priority.value, task_id)
        )
        
        if self.enable_distributed_lock:
            self.locks[task_id] = DistributedLock(f"task_{task_id}")
        
        logger.info(f"Task scheduled: {name} (ID: {task_id}, Priority: {priority.name})")
    
    def schedule_cron(self, task_id: str, name: str, func: Callable, cron_expression: str, **kwargs):
        """使用Cron表达式调度任务"""
        self.schedule(task_id, name, func, cron_expression=cron_expression, **kwargs)
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        self.cancelled_tasks.add(task_id)
        if task_id in self.tasks:
            self.tasks[task_id].state = TaskState.CANCELLED
        logger.info(f"Task cancelled: {task_id}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            'id': task.id,
            'name': task.name,
            'state': task.state.value,
            'priority': task.priority.name,
            'retry_count': task.retry_count,
            'last_run': task.last_run.isoformat() if task.last_run else None,
            'next_run': task.next_run.isoformat() if task.next_run else None,
            'created_at': task.created_at.isoformat()
        }
    
    def _check_dependencies(self, task: ScheduledTask) -> bool:
        """检查任务依赖是否满足"""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False
            dep_task = self.tasks[dep_id]
            if dep_task.state != TaskState.COMPLETED:
                return False
        return True
    
    async def _execute_task(self, task: ScheduledTask) -> bool:
        """执行任务"""
        task_id = task.id
        
        # 获取分布式锁
        lock = self.locks.get(task_id)
        if lock and not lock.acquire():
            logger.warning(f"Could not acquire lock for task: {task_id}")
            return False
        
        try:
            # 检查依赖
            if not self._check_dependencies(task):
                logger.warning(f"Dependencies not met for task: {task_id}")
                return False
            
            # 触发开始事件
            await self.event_callback.emit('on_start', TaskEvent(task_id, 'on_start'))
            
            # 设置超时
            if task.timeout:
                start_time = time.time()
                
                if asyncio.iscoroutinefunction(task.func):
                    task_future = asyncio.create_task(task.func())
                    try:
                        result = await asyncio.wait_for(task_future, timeout=task.timeout)
                    except asyncio.TimeoutError:
                        raise TimeoutError(f"Task {task_id} timed out after {task.timeout}s")
                else:
                    result = task.func()
            else:
                if asyncio.iscoroutinefunction(task.func):
                    result = await task.func()
                else:
                    result = task.func()
            
            task.state = TaskState.COMPLETED
            await self.event_callback.emit('on_success', TaskEvent(task_id, 'on_success', result))
            logger.info(f"Task completed: {task_id}")
            return True
            
        except Exception as e:
            logger.error(f"Task failed: {task_id} - {e}")
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                task.state = TaskState.PENDING
                await self.event_callback.emit('on_retry', TaskEvent(
                    task_id, 'on_retry',
                    {'retry_count': task.retry_count, 'error': str(e)}
                ))
                self.statistics.record_retry()
                
                # 延迟重试
                task.next_run = datetime.now() + timedelta(seconds=task.retry_delay)
                heapq.heappush(
                    self.task_queue,
                    (task.next_run, -task.priority.value, task_id)
                )
                return False
            else:
                task.state = TaskState.FAILED
                await self.event_callback.emit('on_failure', TaskEvent(
                    task_id, 'on_failure', {'error': str(e)}
                ))
                return False
        finally:
            if lock:
                lock.release()
    
    async def run(self):
        """运行调度器"""
        self.running = True
        logger.info("Advanced scheduler started")
        
        while self.running:
            now = datetime.now()
            
            while self.task_queue and self.task_queue[0][0] <= now:
                _, _, task_id = heapq.heappop(self.task_queue)
                
                if task_id not in self.tasks or task_id in self.cancelled_tasks:
                    continue
                
                task = self.tasks[task_id]
                task.state = TaskState.RUNNING
                task.last_run = now
                
                start_time = time.time()
                success = await self._execute_task(task)
                duration = time.time() - start_time
                
                # 记录统计
                self.statistics.record_execution(task_id, duration, success)
                
                # 触发完成事件
                await self.event_callback.emit('on_complete', TaskEvent(
                    task_id, 'on_complete',
                    {'duration': duration, 'success': success}
                ))
                
                # 如果不是周期性任务或已取消，则不重新入队
                if task.state == TaskState.COMPLETED and task.interval_seconds > 0:
                    task.next_run = now + timedelta(seconds=task.interval_seconds)
                    heapq.heappush(
                        self.task_queue,
                        (task.next_run, -task.priority.value, task_id)
                    )
            
            await asyncio.sleep(1)
    
    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info("Advanced scheduler stopped")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        return self.statistics.get_stats()

# 保留原有Scheduler类以保持兼容性
class Scheduler(AdvancedScheduler):
    """调度器 - 兼容旧版API"""
    pass
