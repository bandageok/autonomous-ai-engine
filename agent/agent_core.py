"""Agent Core Module - 自主智能体核心"""
import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib


class AgentState:
    """智能体状态"""
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"


class Task:
    """任务单元"""
    def __init__(self, task_id: str, description: str, priority: int = 5):
        self.id = task_id
        self.description = description
        self.priority = priority
        self.status = "pending"
        self.result = None
        self.created_at = datetime.now()
        self.completed_at = None
        self.error = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error
        }


class AgentCore:
    """自主智能体核心引擎"""

    def __init__(self, name: str, config: Optional[Dict] = None):
        self.name = name
        self.config = config or {}
        self.state = AgentState.IDLE
        self.tasks: List[Task] = []
        self.task_history: List[Dict] = []
        self.memory = {}
        self.tools = {}
        self.llm_provider = None
        self.max_concurrent_tasks = self.config.get("max_concurrent", 3)

    def register_tool(self, name: str, func: callable):
        """注册工具"""
        self.tools[name] = func

    def set_llm_provider(self, provider):
        """设置LLM提供者"""
        self.llm_provider = provider

    async def think(self, prompt: str) -> str:
        """思考过程"""
        self.state = AgentState.THINKING
        try:
            if self.llm_provider:
                response = await self.llm_provider.generate(prompt)
                return response
            return "No LLM provider configured"
        finally:
            self.state = AgentState.IDLE

    async def execute_task(self, task: Task) -> Any:
        """执行单个任务"""
        self.state = AgentState.EXECUTING
        task.status = "running"

        try:
            # 分析任务
            thought = await self.think(f"分析任务: {task.description}")
            task.result = thought

            # 执行任务
            task.status = "completed"
            task.completed_at = datetime.now()

            # 记录历史
            self.task_history.append(task.to_dict())

            return task.result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.now()
            raise

    async def run(self):
        """运行智能体"""
        self.state = AgentState.THINKING
        try:
            while self.tasks:
                task = self.tasks.pop(0)
                await self.execute_task(task)
        finally:
            self.state = AgentState.IDLE
