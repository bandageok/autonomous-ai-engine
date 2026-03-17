"""Workflow Engine - 工作流引擎"""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid

class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    WAITING = "waiting"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str = ""
    name: str = ""
    description: str = ""
    action: Any = None
    handler: Callable = None
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300
    status: StepStatus = StepStatus.WAITING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.name:
            self.name = f"step_{self.id}"

@dataclass
class WorkflowContext:
    """工作流上下文"""
    workflow_id: str
    data: Dict = field(default_factory=dict)
    results: Dict = field(default_factory=dict)
    variables: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class Workflow:
    """工作流定义"""
    id: str = ""
    name: str = ""
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    status: WorkflowStatus = WorkflowStatus.PENDING
    context: Optional[WorkflowContext] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    on_success: Optional[Callable] = None
    on_failure: Optional[Callable] = None

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        if not self.context:
            self.context = WorkflowContext(workflow_id=self.id)

    def add_step(self, step: WorkflowStep):
        """添加步骤"""
        self.steps.append(step)

class WorkflowRegistry:
    """工作流注册表"""
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.templates: Dict[str, Dict] = {}
        
    def register(self, workflow: Workflow):
        """注册工作流"""
        self.workflows[workflow.id] = workflow
        
    def get(self, workflow_id: str) -> Optional[Workflow]:
        """获取工作流"""
        return self.workflows.get(workflow_id)
        
    def list_all(self) -> List[Workflow]:
        """列出所有工作流"""
        return list(self.workflows.values())
        
    def list_by_status(self, status: WorkflowStatus) -> List[Workflow]:
        """按状态列出"""
        return [w for w in self.workflows.values() if w.status == status]

class WorkflowValidator:
    """工作流验证器"""
    
    def __init__(self):
        self.errors: List[str] = []
        
    def validate(self, workflow: Workflow) -> bool:
        """验证工作流"""
        self.errors = []
        
        # 检查步骤
        if not workflow.steps:
            self.errors.append("Workflow has no steps")
            return False
            
        # 检查依赖
        step_ids = {s.id for s in workflow.steps}
        for step in workflow.steps:
            for dep in step.dependencies:
                if dep not in step_ids:
                    self.errors.append(f"Step {step.id} depends on unknown step {dep}")
                    
        # 检查循环依赖
        if self._has_cycle(workflow):
            self.errors.append("Workflow has circular dependencies")
            return False
            
        return len(self.errors) == 0
        
    def _has_cycle(self, workflow: Workflow) -> bool:
        """检查循环依赖"""
        visited = set()
        rec_stack = set()
        
        def visit(step_id: str) -> bool:
            visited.add(step_id)
            rec_stack.add(step_id)
            
            step = next((s for s in workflow.steps if s.id == step_id), None)
            if step:
                for dep in step.dependencies:
                    if dep not in visited:
                        if visit(dep):
                            return True
                    elif dep in rec_stack:
                        return True
                        
            rec_stack.remove(step_id)
            return False
            
        for step in workflow.steps:
            if step.id not in visited:
                if visit(step.id):
                    return True
                    
        return False
        
    def get_errors(self) -> List[str]:
        """获取错误列表"""
        return self.errors

class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.registry = WorkflowRegistry()
        self.validator = WorkflowValidator()
        self.step_handlers: Dict[str, Callable] = {}
        self.running_workflows: Dict[str, asyncio.Task] = {}
        
    def register_handler(self, step_name: str, handler: Callable):
        """注册步骤处理器"""
        self.step_handlers[step_name] = handler
        
    def create_workflow(self, name: str, steps: List[Dict]) -> Workflow:
        """创建工作流"""
        workflow_id = str(uuid.uuid4())[:8]
        
        workflow_steps = []
        for step_data in steps:
            step = WorkflowStep(
                id=step_data.get("id", str(uuid.uuid4())[:8]),
                name=step_data.get("name", "unnamed"),
                description=step_data.get("description", ""),
                handler=step_data.get("handler"),
                dependencies=step_data.get("dependencies", []),
                max_retries=step_data.get("max_retries", 3),
                timeout=step_data.get("timeout", 300)
            )
            workflow_steps.append(step)
            
        workflow = Workflow(
            id=workflow_id,
            name=name,
            steps=workflow_steps
        )
        
        # 验证
        if self.validator.validate(workflow):
            self.registry.register(workflow)
            return workflow
        else:
            raise ValueError(f"Invalid workflow: {self.validator.get_errors()}")
            
    async def execute_step(self, step: WorkflowStep, context: WorkflowContext) -> Any:
        """执行单个步骤"""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()
        
        try:
            # 尝试使用处理器
            handler = step.handler or self.step_handlers.get(step.name)
            
            if handler:
                if asyncio.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(
                        handler(context),
                        timeout=step.timeout
                    )
                else:
                    result = handler(context)
            else:
                result = None
                
            step.status = StepStatus.SUCCESS
            step.result = result
            step.completed_at = datetime.now()
            
            # 存储结果到上下文
            context.results[step.id] = result
            
            return result
            
        except asyncio.TimeoutError:
            step.status = StepStatus.FAILED
            step.error = f"Timeout after {step.timeout}s"
            step.completed_at = datetime.now()
            raise
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.now()
            
            # 重试
            if step.retry_count < step.max_retries:
                step.retry_count += 1
                step.status = StepStatus.WAITING
                return await self.execute_step(step, context)
                
            raise
            
    def _can_execute(self, step: WorkflowStep, completed: set) -> bool:
        """检查步骤是否可以执行"""
        return all(dep in completed for dep in step.dependencies)
        
    async def run(self, workflow_id: str) -> Workflow:
        """运行工作流"""
        workflow = self.registry.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
            
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()
        
        context = workflow.context
        completed = set()
        failed = False
        
        # 拓扑排序执行
        max_iterations = len(workflow.steps) * 2
        iteration = 0
        
        while len(completed) < len(workflow.steps) and iteration < max_iterations:
            iteration += 1
            
            # 找到可执行的步骤
            executable = None
            for step in workflow.steps:
                if step.id not in completed and self._can_execute(step, completed):
                    executable = step
                    break
                    
            if not executable:
                # 检查是否有失败的步骤
                if any(s.status == StepStatus.FAILED for s in workflow.steps):
                    failed = True
                    break
                continue
                
            # 执行步骤
            try:
                await self.execute_step(executable, context)
                completed.add(executable.id)
            except Exception as e:
                failed = True
                break
                
        # 完成工作流
        if failed:
            workflow.status = WorkflowStatus.FAILED
            if workflow.on_failure:
                try:
                    workflow.on_failure(workflow)
                except:
                    pass
        else:
            workflow.status = WorkflowStatus.COMPLETED
            if workflow.on_success:
                try:
                    workflow.on_success(workflow)
                except:
                    pass
                
        workflow.completed_at = datetime.now()
        return workflow
        
    async def run_async(self, workflow_id: str) -> asyncio.Task:
        """异步运行工作流"""
        task = asyncio.create_task(self.run(workflow_id))
        self.running_workflows[workflow_id] = task
        return task
        
    def pause(self, workflow_id: str):
        """暂停工作流"""
        workflow = self.registry.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.RUNNING:
            workflow.status = WorkflowStatus.PAUSED
            
    def resume(self, workflow_id: str):
        """恢复工作流"""
        workflow = self.registry.get(workflow_id)
        if workflow and workflow.status == WorkflowStatus.PAUSED:
            workflow.status = WorkflowStatus.RUNNING
            
    def cancel(self, workflow_id: str):
        """取消工作流"""
        workflow = self.registry.get(workflow_id)
        if workflow:
            workflow.status = WorkflowStatus.CANCELLED
            
            # 取消异步任务
            if workflow_id in self.running_workflows:
                self.running_workflows[workflow_id].cancel()
                
    def get_status(self, workflow_id: str) -> Optional[Dict]:
        """获取工作流状态"""
        workflow = self.registry.get(workflow_id)
        if not workflow:
            return None
            
        return {
            "id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "steps": {
                s.id: {
                    "name": s.name,
                    "status": s.status.value,
                    "result": str(s.result)[:100] if s.result else None,
                    "error": s.error
                }
                for s in workflow.steps
            },
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None
        }

# ==================== 并行工作流执行器 ====================

class ParallelWorkflowExecutor:
    """并行工作流执行器"""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.engine = WorkflowEngine()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
    async def run_parallel(self, workflow_ids: List[str]) -> List[Workflow]:
        """并行运行多个工作流"""
        async def run_with_semaphore(wf_id: str) -> Workflow:
            async with self.semaphore:
                return await self.engine.run(wf_id)
                
        tasks = [run_with_semaphore(wf_id) for wf_id in workflow_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)

# ==================== 工作流模板 ====================

class WorkflowTemplate:
    """工作流模板"""
    
    @staticmethod
    def sequential(name: str, steps: List[str]) -> Dict:
        """顺序工作流模板"""
        return {
            "name": name,
            "steps": [
                {"id": f"step_{i}", "name": step, "dependencies": [] if i == 0 else [f"step_{i-1}"]}
                for i, step in enumerate(steps)
            ]
        }
        
    @staticmethod
    def parallel(name: str, steps: List[str]) -> Dict:
        """并行工作流模板"""
        return {
            "name": name,
            "steps": [
                {"id": f"step_{i}", "name": step, "dependencies": []}
                for i, step in enumerate(steps)
            ]
        }
        
    @staticmethod
    def dag(name: str, dependencies: Dict[str, List[str]]) -> Dict:
        """DAG工作流模板"""
        return {
            "name": name,
            "steps": [
                {"id": step_id, "name": step_id, "dependencies": deps}
                for step_id, deps in dependencies.items()
            ]
        }

# ==================== 工作流监控 ====================

class WorkflowMonitor:
    """工作流监控"""
    
    def __init__(self, engine: WorkflowEngine):
        self.engine = engine
        self.history: List[Dict] = []
        
    def record(self, workflow: Workflow):
        """记录工作流执行"""
        self.history.append({
            "workflow_id": workflow.id,
            "name": workflow.name,
            "status": workflow.status.value,
            "started_at": workflow.started_at.isoformat() if workflow.started_at else None,
            "completed_at": workflow.completed_at.isoformat() if workflow.completed_at else None,
            "duration": (workflow.completed_at - workflow.started_at).total_seconds() 
                        if workflow.started_at and workflow.completed_at else None
        })
        
    def get_stats(self) -> Dict:
        """获取统计"""
        if not self.history:
            return {}
            
        total = len(self.history)
        completed = sum(1 for w in self.history if w["status"] == "completed")
        failed = sum(1 for w in self.history if w["status"] == "failed")
        
        durations = [w["duration"] for w in self.history if w["duration"]]
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "success_rate": completed / total if total > 0 else 0,
            "avg_duration": sum(durations) / len(durations) if durations else 0
        }
