
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
                plan = await self._plan_task(task)
                
                # 执行计划
                result = await self._execute_plan(plan)
                
                task.status = "completed"
                task.result = result
                task.completed_at = datetime.now()
                
                # 记录历史
                self.task_history.append(task.to_dict())
                
                return result
                
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                self.state = AgentState.ERROR
                raise
            finally:
                self.state = AgentState.IDLE
                
        async def _plan_task(self, task: Task) -> Dict:
            """规划任务执行"""
            prompt = f"""分析以下任务，制定执行计划:
任务: {task.description}
            
请返回JSON格式的执行计划:
{{
    "steps": ["步骤1", "步骤2", ...],
    "required_tools": ["tool1", "tool2"],
    "estimated_time": "minutes"
}}"""
            
            response = await self.think(prompt)
            
            try:
                # 尝试解析JSON
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except:
                pass
                
            return {"steps": ["execute_directly"], "required_tools": [], "estimated_time": 1}
            
        async def _execute_plan(self, plan: Dict) -> Any:
            """执行计划"""
            results = []
            
            for step in plan.get("steps", []):
                # 执行每个步骤
                if step in self.tools:
                    result = await self.tools[step]()
                    results.append(result)
                    
            return results
            
        def add_task(self, description: str, priority: int = 5) -> Task:
            """添加新任务"""
            task_id = hashlib.md5(
                f"{description}{datetime.now().isoformat()}".encode()
            ).hexdigest()[:8]
            
            task = Task(task_id, description, priority)
            self.tasks.append(task)
            
            # 按优先级排序
            self.tasks.sort(key=lambda t: t.priority, reverse=True)
            
            return task
            
        async def run(self):
            """运行智能体主循环"""
            while True:
                # 检查待执行任务
                pending = [t for t in self.tasks if t.status == "pending"]
                
                if pending:
                    # 执行最高优先级任务
                    task = pending[0]
                    await self.execute_task(task)
                    
                await asyncio.sleep(1)
                
        def get_status(self) -> Dict:
            """获取状态"""
            return {
                "name": self.name,
                "state": self.state,
                "pending_tasks": len([t for t in self.tasks if t.status == "pending"]),
                "completed_tasks": len([t for t in self.tasks if t.status == "completed"]),
                "total_tasks": len(self.tasks)
            }
