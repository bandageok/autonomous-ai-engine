"""Core Agent - 核心智能体

统一入口：从 agent 模块重新导出
"""
from agent.agent_core import AgentCore, AgentState, Task

__all__ = ['AgentCore', 'AgentState', 'Task']

```python
import asyncio
import logging
import psutil
from enum import Enum, auto
from typing import (
    AsyncGenerator,
    Awaitable,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Union
)

logger = logging.getLogger(__name__)

class AgentState(Enum):
    """Agent 状态机定义"""
    CREATED = auto()
    INITIALIZED = auto()
    RUNNING = auto()
    PAUSED = auto()
    DESTROYED = auto()
    FAILED = auto()

class AgentMessage:
    """Agent 消息队列数据结构"""
    def __init__(self, payload: Dict, priority: int = 0):
        self.payload = payload
        self.priority = priority
        self.timestamp = asyncio.get_event_loop().time()

class AgentLifecycleManager:
    """Agent 生命周期管理器"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.state = AgentState.CREATED
        self._task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._resource_monitor: Optional[ResourceMonitor] = None
        self._fault_tolerance: Optional[FaultToleranceManager] = None
        self._performance_analyzer: Optional[PerformanceAnalyzer] = None

    async def start(self) -> None:
        """启动 Agent 生命周期"""
        if self.state != AgentState.CREATED:
            raise RuntimeError(f"Cannot start Agent {self.agent_id} in state {self.state}")
        
        self.state = AgentState.INITIALIZED
        self._resource_monitor = ResourceMonitor(self.agent_id)
        self._fault_tolerance = FaultToleranceManager(self.agent_id)
        self._performance_analyzer = PerformanceAnalyzer(self.agent_id)
        
        self._heartbeat_task = asyncio.create_task(self._heartbeat())
        self._task = asyncio.create_task(self._run())
        logger.info(f"Agent {self.agent_id} started in state {self.state}")

    async def pause(self) -> None:
        """暂停 Agent 运行"""
        if self.state not in (Agent
```

```python
import asyncio
import psutil
from enum import Enum
from typing import Dict, Any, Optional, List, AsyncGenerator, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

class AgentStatus(Enum):
    """Agent 状态枚举"""
    INIT = "INIT"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"

@dataclass
class ResourceMetrics:
    """资源使用指标"""
    cpu_percent: float
    memory_percent: float
    timestamp: datetime

@dataclass
class PerformanceMetrics:
    """性能分析指标"""
    task_name: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    status: str

class Message:
    """Agent 消息结构"""
    def __init__(self, content: Dict[str, Any], priority: int = 0):
        self.content = content
        self.priority = priority

class AgentMessageQueue:
    """异步消息队列"""
    def __init__(self):
        self._queue: asyncio.Queue[Message] = asyncio.Queue()
        self._priority_queue: asyncio.Queue[Message] = asyncio.Queue()
    
    async def put(self, message: Message):
        """异步放入消息"""
        if message.priority > 0:
            await self._priority_queue.put(message)
        else:
            await self._queue.put(message)
    
    async def get(self) -> Message:
        """异步获取最高优先级消息"""
        if not self._priority_queue.empty():
            return await self._priority_queue.get()
        return await self._queue.get()
    
    def qsize(self) -> int:
        """获取消息数量"""
        return self._priority_queue.qsize() + self._queue.qsizemp()

class AgentLifecycleManager:
    """Agent 生命周期管理器"""
    def __init__(self, agent: "Agent"):
        self.agent = agent
        self._state = AgentStatus.INIT
        self._state_transitions: Dict[AgentStatus, List[AgentStatus]] = {
            AgentStatus.INIT: [AgentStatus.RUNNING, AgentStatus.STOPPED],
            AgentStatus.RUNNING: [AgentStatus.PAUSED, AgentStatus.STOPPED, AgentStatus.FAILED],
            AgentStatus.PAUSED: [AgentStatus.RUNNING, AgentStatus.STOPPED],
            AgentStatus.STOPPED: [AgentStatus.INIT, Agent
```