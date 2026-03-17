"""Task Planner - 任务规划器"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import heapq


class TaskPriority:
    """任务优先级"""
    CRITICAL = 10
    HIGH = 7
    MEDIUM = 5
    LOW = 3
    IDLE = 1


class Dependency:
    """任务依赖"""
    def __init__(self, task_id: str, depends_on: List[str]):
        self.task_id = task_id
        self.depends_on = depends_on


class TaskGraph:
    """任务依赖图"""

    def __init__(self):
        self.nodes: Dict[str, Dict] = {}
        self.edges: Dict[str, List[str]] = {}

    def add_task(self, task_id: str, metadata: Optional[Dict] = None):
        """添加任务节点"""
        self.nodes[task_id] = metadata or {}
        if task_id not in self.edges:
            self.edges[task_id] = []

    def add_dependency(self, from_task: str, to_task: str):
        """添加依赖边"""
        if from_task in self.edges:
            self.edges[from_task].append(to_task)

    def topological_sort(self) -> List[str]:
        """拓扑排序"""
        in_degree = {node: 0 for node in self.nodes}

        for node in self.edges:
            for neighbor in self.edges[node]:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1

        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            node = heapq.heappop(queue)
            result.append(node)

            if node in self.edges:
                for neighbor in self.edges[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        heapq.heappush(queue, neighbor)

        return result


class TaskScheduler:
    """任务调度器"""

    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.pending_tasks: List[Tuple[int, Task]] = []
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: Dict[str, Task] = {}

    def add_task(self, task):
        """添加任务"""
        priority = getattr(task, 'priority', TaskPriority.MEDIUM)
        heapq.heappush(self.pending_tasks, (-priority, task))

    def get_next_task(self):
        """获取下一个任务"""
        if self.pending_tasks and len(self.running_tasks) < self.max_concurrent:
            _, task = heapq.heappop(self.pending_tasks)
            return task
        return None
