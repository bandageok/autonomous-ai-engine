"""Core Planner - 规划器

统一入口：从 agent 模块重新导出
"""
from agent.task_planner import TaskGraph, TaskPriority, Dependency, TaskScheduler

__all__ = ['TaskGraph', 'TaskPriority', 'Dependency', 'TaskScheduler']

```python
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator, Set, Callable
import asyncio
import heapq
import uuid
import time
from dataclasses import dataclass

@dataclass
class Task:
    """任务基类，包含任务的基本属性"""
    task_id: str
    name: str
    description: str
    dependencies: Set[str]
    resources: Dict[str, float]
    estimated_time: float
    priority: int = 0
    status: str = "PENDING"
    checkpoint: Dict[str, Any] = None

class TaskDecomposer:
    """任务分解器，将复杂任务分解为子任务"""
    
    def __init__(self):
        self.decomposition_rules = {
            "complex_analysis": self._decompose_analysis,
            "data_processing": self._decompose_data,
            "system_integration": self._decompose_integration
        }
    
    async def decompose(self, task: Task) -> List[Task]:
        """
        异步分解任务为子任务
        
        Args:
            task: 需要分解的主任务
            
        Returns:
            List[Task]: 分解后的子任务列表
        """
        decomposed_tasks = []
        decomposition_method = self._select_decomposition_method(task)
        
        if decomposition_method:
            sub_tasks = decomposition_method(task)
            decomposed_tasks.extend(sub_tasks)
            return decomposed_tasks
        
        return [task]
    
    def _select_decomposition_method(self, task: Task) -> Callable[[Task], List[Task]]:
        """选择合适的分解方法"""
        if task.name in self.decomposition_rules:
            return self.decomposition_rules[task.name]
        return lambda t: [t]
    
    def _decompose_analysis(self, task: Task) -> List[Task]:
        """分解分析型任务"""
        return [
            Task(
                str(uuid.uuid4()),
                f"{task.name}_data_collection",
                "收集分析所需数据",
                set(),
                {"cpu": 0.5, "memory": 2.0},
                10.0
            ),
            Task(
                str(uuid.uuid4()),
                f"{task.name}_pattern_recognition",
                "识别数据模式",
                set(),
                {"cpu": 1.0, "memory": 3.0},
                15.0
            ),
            Task(
                str(uuid.uuid4()),
                f"{task.name}_report_generation",
                "生成分析报告",
                set(),
                {"cpu": 0.5, "memory": 1.5},
                5.0
            )
        ]
    
    def _decompose_data(self, task: Task) -> List[Task]:
        """分解数据处理任务"""
        return [
            Task(
                str(uuid.uuid4()),
                f"{task.name}_data_cleaning",
                "清洗数据",
                set(),
                {"cpu": 0.8, "memory": 4.0},
                20.0
            ),
            Task(
                str. uuid4(),
                f"{task.name}_data_transform",
                "数据转换",
                set(),
                {"cpu": 1.2, "memory": 5.0},
                25.0
            ),
            Task(
                str(uuid.uuid4()),
                f"{task.name}_data_storage",
                "存储处理后的数据",
                set(),
                {"cpu": 0.5, "memory": 2.0},
                10.0
            )
        ]
    
    def _decompose_integration(self, task: Task) -> List[Task]:
        """分解系统集成任务"""
        return [
            Task(
                str(uuid.uuid4()),
                f"{task.name}_api_integration",
                "集成API接口",
                set(),
                {"cpu": 1.0, "memory": 3.0},
                15.0
            ),
            Task(
                str(uuid.uuid4()),
                f"{task.name}_database_sync",
                "数据库同步",
                set(),
                {"cpu": 0.8, "memory": 4.0},
                20.0
            ),
            Task(
                str(uuid.uuid4()),
                f"{task.name}_security_setup",
                "设置安全机制",
                set(),
                {"cpu": 0.7, "memory": 2.5},
                12.0
            )
        ]

class PriorityScheduler:
    """任务优先级调度器，基于多种因素计算优先级"""
    
    def __init__(self):
        self.priority_factors = {
            "urgency": 0.4,
            "complexity": 0.3,
            "resource_demand": 0.2,
            "dependency_count": 0.1
        }
    
    async def schedule(self, tasks: List[Task]) -> List[Task]:
        """
        异步调度任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            List[Task]: 按优先级排序的任务列表
        """
        # 计算优先级
        for task in tasks:
            task.priority = self._calculate_priority(task)
        
        # 使用堆排序
        priority_heap = [(task.priority, task) for task in tasks]
        heapq.heapify(priority_heap)
        
        return [heapq.heappop(priority_heap)[1] for _ in range(len(priority_heap))]
    
    def _calculate_priority(self, task: Task) -> float:
        """计算任务优先级"""
        urgency = 1.0 / (task.estimated_time + 1)
        complexity = len(task.dependencies) * 0.5
        resource_demand = sum(task.resources.values()) * 0.1
        dependency_count = len(task.dependencies)
        
        return (
            self.priority_factors["urgency"] * urgency +
            self.priority_factors["complexity"] * complexity +
            self.priority_factors["resource_demand"] * resource_demand +
            self.priority_factors["dependency_count"] * dependency_count
        )

class DependencyGraph:
    """任务依赖图，管理任务间依赖关系"""
    
    def __init__(self):
        self.graph = {}
        self.in_degree = {}
    
    async def add_dependency(self, task: Task, dependent_task: Task) -> None:
        """
        添加任务依赖关系
        
        Args:
            task: 依赖任务
            dependent_task: 依赖该任务的任务
        """
        if task.task_id not in self.graph:
            self.graph[task.task_id] = []
        if dependent_task.task_id not in self.graph:
            self.graph[dependent_task.task_id] = []
        
        self.graph[task.task_id].append(dependent_task.task_id)
        self.in_degree[dependent_task.task_id] = self.in_degree.get(dependent_task.task_id, 0) + 1
    
    async def check_cycle(self) -> bool:
        """检查依赖图是否存在循环"""
        visited = set()
        recursion_stack = set()
        
        async def _check_cycle(node: str) -> bool:
            if node in recursion_stack:
                return True
            if node in visited:
                return False
            
            recursion_stack.add(node)
            for neighbor in self.graph.get(node, []):
                if await _check_cycle(neighbor):
                    return True
            recursion_stack.remove(node)
            visited.add(node)
            return False
        
        for node in self.graph:
            if await _check_cycle(node):
                return True
        return False

class TimeEstimator:
    """任务时间估计器，预测任务执行时间"""
    
    def __init__(self):
        self.time_factors = {
            "base_time": 1.0,
            "resource_multiplier": 1.2,
            "parallelism_bonus": 0.8
        }
    
    async def estimate_time(self, task: Task, resources: Dict[str, float]) -> float:
        """
        估计任务执行时间
        
        Args:
            task: 任务对象
            resources: 可用资源
            
        Returns:
            float: 估计的执行时间（秒）
        """
        base_time = task.estimated_time
        resource_multiplier = self._calculate_resource_multiplier(task, resources)
        parallelism_bonus = self._calculate_parallelism_bonus(task, resources)
        
        return base_time * resource_multiplier * parallelism_bonus
    
    def _calculate_resource_multiplier(self, task: Task, resources: Dict[str, float]) -> float:
        """计算资源乘数"""
        if not resources:
            return 1.0
            
        total_resource = sum(resources.values())
        task_resource = sum(task.resources.values())
        
        if total_resource == 0:
            return 1.0
            
        return (total_resource / task_resource) ** 0.5
    
    def _calculate_parallelism_bonus(self, task: Task, resources: Dict[str, float]) -> float:
        """计算并行加速系数"""
        if not resources:
            return 1.0
            
        available_cores = resources.get("cpu", 0)
        task_cores = task.resources.get("cpu", 1)
        
        if available_cores == 0:
            return 1.0
            
        return min(1.0, (available_cores / task_cores) * 0.8)

class ResourceAllocator:
    """任务资源分配器，智能分配计算资源"""
    
    def __init__(self):
        self.available_resources = {
            "cpu": 8.0,
            "memory": 16.0
        }
    
    async def allocate_resources(self, tasks: List[Task]) -> Dict[str, Dict[str, float]]:
        """
        异步分配资源给任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            Dict[str, Dict[str, float]]: 资源分配方案
        """
        # 按优先级排序
        priority_scheduler = PriorityScheduler()
        sorted_tasks = await priority_scheduler.schedule(tasks)
        
        allocation = {}
        remaining_resources = self.available_resources.copy()
        
        for task in sorted_tasks:
            if task.status != "PENDING":
                continue
                
            # 计算资源需求
            required_resources = task.resources.copy()
            
            # 检查资源是否足够
            if all(remaining_resources[key] >= required_resources[key] for key in required_resources):
                # 分配资源
                for resource, amount in required_resources.items():
                    remaining_resources[resource] -= amount
                allocation[task.task_id] = required_resources
            else:
                # 调整资源需求
                adjusted_resources = {}
                for resource, amount in required_resources.items():
                    if remaining_resources[resource] > 0:
                        adjusted_resources[resource] = remaining_resources[resource]
                        remaining_resources[resource] = 0
                allocation[task.task_id] = adjusted_resources
        
        return allocation

class CheckpointManager:
    """任务回滚机制，失败时回滚到检查点"""
    
    def __init__(self):
        self.checkpoints = {}
    
    async def record_checkpoint(self, task: Task, state: Dict[str, Any]) -> None:
        """记录检查点"""
        self.checkpoints[task.task_id] = {
            "timestamp": time.time(),
            "state": state,
            "dependencies": {dep.task_id: dep.status for dep in task.dependencies}
        }
    
    async def rollback(self, task: Task) -> None:
        """回滚到最近的检查点"""
        if task.task_id not in self.checkpoints:
            return
            
        checkpoint = self.checkpoints[task.task_id]
        # 恢复状态
        for dep_id, dep_status in checkpoint["dependencies"].items():
            await self._set_task_status(dep_id, dep_status)
        
        # 恢复任务状态
        task.status = "PENDING"
        # 清除后续检查点
        for pid in list(self.checkpoints.keys()):
            if pid > task.task_id:
                del self.checkpoints[pid]
    
    async def _set_task_status(self, task_id: str, status: str) -> None:
        """设置任务状态"""
        # 实际实现中应更新任务状态
        print(f"Setting task {task_id} status to {status}")

class TaskOptimizer:
    """任务最优化器，寻找最优执行路径"""
    
    def __init__(self):
        self.optimization_factors = {
            "time_weight": 0.6,
            "resource_weight": 0.3,
            "priority_weight": 0.1
        }
    
    async def optimize_schedule(self, tasks: List[Task]) -> List[Task]:
        """
        异步优化任务执行顺序
        
        Args:
            tasks: 任务列表
            
        Returns:
            List[Task]: 优化后的任务顺序
        """
        # 计算任务权重
        for task in tasks:
            task.weight = self._calculate_task_weight(task)
        
        # 使用Dijkstra算法寻找最优路径
        return self._dijkstra(tasks)
    
    def _calculate_task_weight(self, task: Task) -> float:
        """计算任务权重"""
        time_weight = task.estimated_time * self.optimization_factors["time_weight"]
        resource_weight = sum(task.resources.values()) * self.optimization_factors["resource_weight"]
        priority_weight = task.priority * self.optimization_factors["priority_weight"]
        
        return time_weight + resource_weight + priority_weight
    
    def _dijkstra(self, tasks: List[Task]) -> List[Task]:
        """Dijkstra算法寻找最优路径"""
        # 简化实现，实际应构建图结构
        return sorted(tasks, key=lambda t: t.weight)
```