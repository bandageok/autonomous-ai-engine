"""Multi-Agent System - 多智能体系统"""
import asyncio
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

class AgentRole(Enum):
    COORDINATOR = "coordinator"
    WORKER = "worker"
    MONITOR = "monitor"
    PLANNER = "planner"
    EXECUTOR = "executor"

class MessageType(Enum):
    TASK = "task"
    RESULT = "result"
    QUERY = "query"
    RESPONSE = "response"
    BROADCAST = "broadcast"
    HEARTBEAT = "heartbeat"

@dataclass
class AgentMessage:
    """智能体消息"""
    id: str
    sender_id: str
    receiver_id: Optional[str]
    message_type: MessageType
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

@dataclass
class AgentCapability:
    """智能体能力"""
    name: str
    description: str
    handler: Callable

class AgentProfile:
    """智能体配置"""
    def __init__(self, agent_id: str, name: str, role: AgentRole, capabilities: List[str]):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.capabilities = capabilities
        self.status: str = "idle"
        self.load: float = 0.0

class BaseAgent:
    """基础智能体"""
    
    def __init__(self, profile: AgentProfile):
        self.profile = profile
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.inbox: List[AgentMessage] = []
        self.outbox: List[AgentMessage] = []
        self.running = False
        self.task_handlers: Dict[str, Callable] = {}
        
    async def start(self):
        """启动智能体"""
        self.running = True
        asyncio.create_task(self._process_messages())
        
    async def stop(self):
        """停止智能体"""
        self.running = False
        
    async def send_message(self, receiver_id: str, content: Any, 
                          msg_type: MessageType = MessageType.TASK):
        """发送消息"""
        message = AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=self.profile.agent_id,
            receiver_id=receiver_id,
            message_type=msg_type,
            content=content
        )
        self.outbox.append(message)
        return message
        
    async def broadcast(self, content: Any, msg_type: MessageType = MessageType.BROADCAST):
        """广播消息"""
        return await self.send_message(None, content, msg_type)
        
    async def receive_message(self, message: AgentMessage):
        """接收消息"""
        self.inbox.append(message)
        await self.message_queue.put(message)
        
    async def _process_messages(self):
        """处理消息"""
        while self.running:
            try:
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )
                await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
                
    async def _handle_message(self, message: AgentMessage):
        """处理单个消息"""
        handler_key = f"{message.message_type.value}"
        handler = self.task_handlers.get(handler_key)
        
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                print(f"Handler error: {e}")
                
    def register_handler(self, message_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self.task_handlers[message_type.value] = handler

class CoordinatorAgent(BaseAgent):
    """协调者智能体"""
    
    def __init__(self, profile: AgentProfile):
        super().__init__(profile)
        self.workers: Dict[str, BaseAgent] = {}
        self.task_queue: Dict[str, List[str]] = {}  # task_id -> worker_ids
        
    def register_worker(self, worker: BaseAgent):
        """注册工作智能体"""
        self.workers[worker.profile.agent_id] = worker
        
    async def assign_task(self, task: Dict, worker_id: str = None) -> str:
        """分配任务"""
        task_id = str(uuid.uuid4())
        
        if worker_id:
            # 指定worker
            worker = self.workers.get(worker_id)
            if worker:
                await worker.receive_message(AgentMessage(
                    id=str(uuid.uuid4()),
                    sender_id=self.profile.agent_id,
                    receiver_id=worker_id,
                    message_type=MessageType.TASK,
                    content=task
                ))
        else:
            # 自动分配负载最低的worker
            min_load_worker = min(
                self.workers.values(),
                key=lambda w: w.profile.load
            )
            await min_load_worker.receive_message(AgentMessage(
                id=str(uuid.uuid4()),
                sender_id=self.profile.agent_id,
                receiver_id=min_load_worker.profile.agent_id,
                message_type=MessageType.TASK,
                content=task
            ))
            
        return task_id
        
    async def broadcast_task(self, task: Dict):
        """广播任务给所有worker"""
        for worker in self.workers.values():
            await worker.receive_message(AgentMessage(
                id=str(uuid.uuid4()),
                sender_id=self.profile.agent_id,
                receiver_id=worker.profile.agent_id,
                message_type=MessageType.TASK,
                content=task
            ))

class WorkerAgent(BaseAgent):
    """工作智能体"""
    
    def __init__(self, profile: AgentProfile):
        super().__init__(profile)
        self.current_task: Optional[Dict] = None
        
    async def execute_task(self, task: Dict) -> Any:
        """执行任务"""
        self.profile.status = "working"
        self.current_task = task
        
        try:
            # 模拟任务执行
            task_type = task.get("type", "default")
            handler = self.task_handlers.get(task_type)
            
            if handler:
                result = await handler(task) if asyncio.iscoroutinefunction(handler) else handler(task)
            else:
                result = {"status": "completed", "result": "No handler"}
                
            self.profile.status = "idle"
            return result
            
        except Exception as e:
            self.profile.status = "error"
            return {"status": "failed", "error": str(e)}
        finally:
            self.current_task = None

class MonitorAgent(BaseAgent):
    """监控智能体"""
    
    def __init__(self, profile: AgentProfile):
        super().__init__(profile)
        self.agent_states: Dict[str, Dict] = {}
        self.metrics: Dict[str, List[float]] = {}
        
    async def monitor_agent(self, agent_id: str):
        """监控智能体状态"""
        return self.agent_states.get(agent_id)
        
    async def get_all_states(self) -> Dict[str, Dict]:
        """获取所有状态"""
        return self.agent_states
        
    async def record_metric(self, metric_name: str, value: float):
        """记录指标"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)
        
    async def get_metric_stats(self, metric_name: str) -> Dict:
        """获取指标统计"""
        values = self.metrics.get(metric_name, [])
        if not values:
            return {}
            
        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values)
        }

class MultiAgentSystem:
    """多智能体系统"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.coordinator: Optional[CoordinatorAgent] = None
        self.monitor: Optional[MonitorAgent] = None
        self.message_bus: asyncio.Queue = asyncio.Queue()
        
    def register_agent(self, agent: BaseAgent):
        """注册智能体"""
        self.agents[agent.profile.agent_id] = agent
        
        if isinstance(agent, CoordinatorAgent):
            self.coordinator = agent
        elif isinstance(agent, MonitorAgent):
            self.monitor = agent
            
    async def start_all(self):
        """启动所有智能体"""
        for agent in self.agents.values():
            await agent.start()
            
    async def stop_all(self):
        """停止所有智能体"""
        for agent in self.agents.values():
            await agent.stop()
            
    async def submit_task(self, task: Dict, worker_id: str = None) -> str:
        """提交任务"""
        if not self.coordinator:
            raise RuntimeError("No coordinator available")
            
        return await self.coordinator.assign_task(task, worker_id)
        
    async def broadcast(self, message: Any):
        """广播消息"""
        for agent in self.agents.values():
            if agent != self.coordinator:
                await agent.broadcast(message)
                
    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """获取智能体"""
        return self.agents.get(agent_id)
        
    def list_agents(self, role: AgentRole = None) -> List[BaseAgent]:
        """列出智能体"""
        if role:
            return [a for a in self.agents.values() if a.profile.role == role]
        return list(self.agents.values())
        
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        return {
            "total_agents": len(self.agents),
            "coordinator": self.coordinator.profile.name if self.coordinator else None,
            "workers": len([a for a in self.agents.values() if a.profile.role == AgentRole.WORKER]),
            "agents": {
                agent_id: {
                    "name": agent.profile.name,
                    "role": agent.profile.role.value,
                    "status": agent.profile.status,
                    "load": agent.profile.load
                }
                for agent_id, agent in self.agents.items()
            }
        }

# ==================== 智能体通信协议 ====================

class AgentProtocol:
    """智能体通信协议"""
    
    @staticmethod
    def create_task_message(sender_id: str, receiver_id: str, task: Dict) -> AgentMessage:
        """创建任务消息"""
        return AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.TASK,
            content=task
        )
        
    @staticmethod
    def create_result_message(sender_id: str, receiver_id: str, result: Any) -> AgentMessage:
        """创建结果消息"""
        return AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.RESULT,
            content=result
        )
        
    @staticmethod
    def create_query_message(sender_id: str, receiver_id: str, query: str) -> AgentMessage:
        """创建查询消息"""
        return AgentMessage(
            id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=MessageType.QUERY,
            content=query
        )

# ==================== 智能体工厂 ====================

class AgentFactory:
    """智能体工厂"""
    
    @staticmethod
    def create_coordinator(name: str = "coordinator") -> CoordinatorAgent:
        """创建协调者"""
        profile = AgentProfile(
            agent_id=str(uuid.uuid4())[:8],
            name=name,
            role=AgentRole.COORDINATOR,
            capabilities=["task_assignment", "resource_allocation", "conflict_resolution"]
        )
        return CoordinatorAgent(profile)
        
    @staticmethod
    def create_worker(name: str = "worker", capabilities: List[str] = None) -> WorkerAgent:
        """创建工作者"""
        profile = AgentProfile(
            agent_id=str(uuid.uuid4())[:8],
            name=name,
            role=AgentRole.WORKER,
            capabilities=capabilities or ["task_execution", "data_processing"]
        )
        return WorkerAgent(profile)
        
    @staticmethod
    def create_monitor(name: str = "monitor") -> MonitorAgent:
        """创建监控者"""
        profile = AgentProfile(
            agent_id=str(uuid.uuid4())[:8],
            name=name,
            role=AgentRole.MONITOR,
            capabilities=["health_check", "metrics_collection", "alerting"]
        )
        return MonitorAgent(profile)
