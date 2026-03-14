"""Core Planner - 规划器"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

class PlanStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class PlanStep:
    """规划步骤"""
    id: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    status: PlanStatus = PlanStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class Plan:
    """规划"""
    id: str
    goal: str
    steps: List[PlanStep]
    status: PlanStatus = PlanStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    context: Dict = field(default_factory=dict)

class GoalDecomposer:
    """目标分解器"""
    
    def __init__(self, llm_provider=None):
        self.llm = llm_provider
        
    async def decompose(self, goal: str) -> List[str]:
        """分解目标"""
        if not self.llm:
            # 默认分解
            return [f"Step {i+1}: {goal}" for i in range(3)]
            
        # 使用LLM分解
        prompt = f"""Break down this goal into clear, actionable steps:
Goal: {goal}

Provide steps as a numbered list."""
        
        response = await self.llm.generate(prompt)
        
        # 解析响应
        steps = []
        for line in response.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                steps.append(line)
                
        return steps if steps else [goal]

class PlanExecutor:
    """规划执行器"""
    
    def __init__(self):
        self.plans: Dict[str, Plan] = {}
        self.step_handlers: Dict[str, Callable] = {}
        
    def register_handler(self, step_type: str, handler: Callable):
        """注册步骤处理器"""
        self.step_handlers[step_type] = handler
        
    async def execute_plan(self, plan_id: str) -> Plan:
        """执行规划"""
        if plan_id not in self.plans:
            raise ValueError(f"Plan not found: {plan_id}")
            
        plan = self.plans[plan_id]
        plan.status = PlanStatus.IN_PROGRESS
        
        for step in plan.steps:
            # 检查依赖
            if not self._can_execute(step, plan):
                step.status = PlanStatus.FAILED
                step.error = "Dependencies not met"
                continue
                
            # 执行步骤
            step.status = PlanStatus.IN_PROGRESS
            step.started_at = datetime.now()
            
            try:
                handler = self.step_handlers.get(step.description.split()[0])
                if handler:
                    step.result = await handler(step)
                else:
                    step.result = "No handler"
                    
                step.status = PlanStatus.COMPLETED
                step.completed_at = datetime.now()
                
            except Exception as e:
                step.status = PlanStatus.FAILED
                step.error = str(e)
                step.completed_at = datetime.now()
                
        # 检查完成状态
        if all(s.status == PlanStatus.COMPLETED for s in plan.steps):
            plan.status = PlanStatus.COMPLETED
        else:
            plan.status = PlanStatus.FAILED
            
        return plan
        
    def _can_execute(self, step: PlanStep, plan: Plan) -> bool:
        """检查是否可以执行"""
        for dep_id in step.dependencies:
            dep_step = next((s for s in plan.steps if s.id == dep_id), None)
            if not dep_step or dep_step.status != PlanStatus.COMPLETED:
                return False
        return True
        
    def create_plan(self, plan_id: str, goal: str, steps: List[str]) -> Plan:
        """创建规划"""
        plan_steps = []
        for i, step_desc in enumerate(steps):
            step = PlanStep(
                id=f"{plan_id}_step_{i}",
                description=step_desc
            )
            plan_steps.append(step)
            
        plan = Plan(id=plan_id, goal=goal, steps=plan_steps)
        self.plans[plan_id] = plan
        
        return plan
