
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
            
        def get_critical_path(self) -> List[str]:
            """获取关键路径"""
            # 简化的关键路径计算
            sorted_tasks = self.topological_sort()
            return sorted_tasks
            
    class TaskPlanner:
        """智能任务规划器"""
        
        def __init__(self):
            self.graph = TaskGraph()
            self.task_registry: Dict[str, Dict] = {}
            
        def plan(self, goal: str, constraints: Optional[Dict] = None) -> Dict:
            """制定任务计划"""
            constraints = constraints or {}
            
            # 分解目标为子任务
            subtasks = self._decompose_goal(goal)
            
            # 确定依赖关系
            dependencies = self._resolve_dependencies(subtasks)
            
            # 构建任务图
            for task in subtasks:
                self.graph.add_task(task["id"], task)
                
            for dep in dependencies:
                self.graph.add_dependency(dep[0], dep[1])
                
            # 排序
            execution_order = self.graph.topological_sort()
            
            return {
                "goal": goal,
                "subtasks": subtasks,
                "execution_order": execution_order,
                "estimated_duration": len(subtasks) * 5,  # 分钟
                "constraints": constraints
            }
            
        def _decompose_goal(self, goal: str) -> List[Dict]:
            """分解目标为子任务"""
            # 简单的分解逻辑
            subtasks = []
            
            # 常见任务模式
            patterns = [
                ("research", "调研阶段", TaskPriority.MEDIUM),
                ("design", "设计阶段", TaskPriority.HIGH),
                ("implement", "实现阶段", TaskPriority.HIGH),
                ("test", "测试阶段", TaskPriority.MEDIUM),
                ("deploy", "部署阶段", TaskPriority.LOW),
                ("optimize", "优化阶段", TaskPriority.IDLE),
            ]
            
            for i, (pattern, desc, priority) in enumerate(patterns):
                if pattern in goal.lower() or i == 0:  # 至少添加一个
                    subtasks.append({
                        "id": f"task_{i}_{pattern}",
                        "name": f"{desc}: {goal}",
                        "priority": priority,
                        "estimated_time": 10 + i * 5
                    })
                    
            return subtasks
            
        def _resolve_dependencies(self, subtasks: List[Dict]) -> List[Tuple[str, str]]:
            """解析任务依赖"""
            dependencies = []
            
            # 顺序依赖
            for i in range(len(subtasks) - 1):
                dependencies.append((
                    subtasks[i]["id"],
                    subtasks[i + 1]["id"]
                ))
                
            return dependencies
            
        def optimize_plan(self, plan: Dict) -> Dict:
            """优化任务计划"""
            # 并行化独立任务
            execution_order = plan.get("execution_order", [])
            
            # 找出可以并行的任务
            parallelizable = []
            
            return {
                **plan,
                "optimized_order": execution_order,
                "parallel_groups": parallelizable
            }
