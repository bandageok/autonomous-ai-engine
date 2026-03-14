"""Scheduler Module - 任务调度器"""
import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import heapq

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ScheduledTask:
    """计划任务"""
    id: str
    name: str
    func: Callable
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0

class TaskScheduler:
    """任务调度器"""
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List = []
        self.running = False
        
    def schedule(self, task_id: str, name: str, func: Callable, interval_seconds: int = 3600):
        """调度任务"""
        task = ScheduledTask(task_id, name, func)
        task.next_run = datetime.now() + timedelta(seconds=interval_seconds)
        self.tasks[task_id] = task
        heapq.heappush(self.task_queue, (task.next_run, task_id))
        
    def unschedule(self, task_id: str) -> bool:
        """取消调度"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False
        
    async def run(self):
        """运行调度器"""
        self.running = True
        while self.running:
            now = datetime.now()
            while self.task_queue and self.task_queue[0][0] <= now:
                _, task_id = heapq.heappop(self.task_queue)
                if task_id not in self.tasks:
                    continue
                task = self.tasks[task_id]
                task.status = TaskStatus.RUNNING
                task.last_run = now
                try:
                    if asyncio.iscoroutinefunction(task.func):
                        await task.func()
                    else:
                        task.func()
                    task.status = TaskStatus.COMPLETED
                    task.run_count += 1
                except Exception as e:
                    task.status = TaskStatus.FAILED
                task.next_run = now + timedelta(hours=1)
                heapq.heappush(self.task_queue, (task.next_run, task_id))
            await asyncio.sleep(1)
            
    def stop(self):
        """停止调度器"""
        self.running = False
