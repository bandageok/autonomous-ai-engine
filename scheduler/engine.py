"""Scheduler Engine - 调度引擎"""
import asyncio
from typing import Dict, List, Callable, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import heapq

class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ScheduledTask:
    """计划任务"""
    id: str
    name: str
    func: Callable
    interval_seconds: int
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    state: TaskState = TaskState.PENDING

class Scheduler:
    """调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[tuple] = []  # (next_run_time, task_id)
        self.running = False
        
    def schedule(self, task_id: str, name: str, func: Callable, interval_seconds: int = 3600):
        """调度任务"""
        task = ScheduledTask(
            id=task_id,
            name=name,
            func=func,
            interval_seconds=interval_seconds,
            next_run=datetime.now() + timedelta(seconds=interval_seconds)
        )
        
        self.tasks[task_id] = task
        heapq.heappush(self.task_queue, (task.next_run, task_id))
        
    async def run(self):
        """运行"""
        self.running = True
        
        while self.running:
            now = datetime.now()
            
            while self.task_queue and self.task_queue[0][0] <= now:
                _, task_id = heapq.heappop(self.task_queue)
                
                if task_id not in self.tasks:
                    continue
                    
                task = self.tasks[task_id]
                task.state = TaskState.RUNNING
                task.last_run = now
                
                try:
                    if asyncio.iscoroutinefunction(task.func):
                        await task.func()
                    else:
                        task.func()
                    task.state = TaskState.COMPLETED
                except Exception as e:
                    task.state = TaskState.FAILED
                    
                task.next_run = now + timedelta(seconds=task.interval_seconds)
                heapq.heappush(self.task_queue, (task.next_run, task_id))
                
            await asyncio.sleep(1)
            
    def stop(self):
        """停止"""
        self.running = False
