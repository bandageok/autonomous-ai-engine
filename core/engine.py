"""Core Engine - 核心引擎"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class EngineState(Enum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class EngineConfig:
    """引擎配置"""
    max_concurrent_tasks: int = 10
    default_timeout: int = 300
    retry_attempts: int = 3
    enable_monitoring: bool = True
    log_level: str = "INFO"

@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: str
    result: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    metadata: Dict = field(default_factory=dict)

class TaskQueue:
    """任务队列"""
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.results: Dict[str, TaskResult] = {}
        
    async def put(self, task_id: str, data: Any):
        """添加任务"""
        await self.queue.put((task_id, data))
        
    async def get(self) -> tuple:
        """获取任务"""
        return await self.queue.get()
    
    def mark_done(self, task_id: str, result: TaskResult):
        """标记完成"""
        self.results[task_id] = result
        
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """获取结果"""
        return self.results.get(task_id)

class EventBus:
    """事件总线"""
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        
    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
        
    async def publish(self, event_type: str, data: Any):
        """发布事件"""
        if event_type in self.subscribers:
            for handler in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(data)
                    else:
                        handler(data)
                except Exception as e:
                    logger.error(f"Event handler error: {e}")

class Plugin:
    """插件基类"""
    def __init__(self, name: str):
        self.name = name
        self.enabled = False
        
    async def initialize(self, engine: 'AIEngine'):
        """初始化"""
        pass
        
    async def execute(self, context: Dict) -> Any:
        """执行"""
        pass
        
    async def shutdown(self):
        """关闭"""
        pass

class AIEngine:
    """AI引擎"""
    
    def __init__(self, config: Optional[EngineConfig] = None):
        self.config = config or EngineConfig()
        self.state = EngineState.IDLE
        self.task_queue = TaskQueue()
        self.event_bus = EventBus()
        self.plugins: Dict[str, Plugin] = {}
        self.context: Dict = {}
        self.start_time: Optional[datetime] = None
        
    def register_plugin(self, plugin: Plugin):
        """注册插件"""
        self.plugins[plugin.name] = plugin
        logger.info(f"Registered plugin: {plugin.name}")
        
    async def initialize(self):
        """初始化引擎"""
        self.state = EngineState.INITIALIZING
        logger.info("Initializing AI Engine...")
        
        # 初始化插件
        for name, plugin in self.plugins.items():
            await plugin.initialize(self)
            plugin.enabled = True
            
        self.state = EngineState.IDLE
        self.start_time = datetime.now()
        logger.info("AI Engine initialized")
        
    async def start(self):
        """启动引擎"""
        if self.state != EngineState.IDLE:
            raise RuntimeError(f"Cannot start from state: {self.state}")
            
        self.state = EngineState.RUNNING
        logger.info("AI Engine started")
        
        # 启动任务处理循环
        asyncio.create_task(self._process_tasks())
        
    async def stop(self):
        """停止引擎"""
        self.state = EngineState.STOPPED
        
        # 关闭插件
        for plugin in self.plugins.values():
            await plugin.shutdown()
            
        logger.info("AI Engine stopped")
        
    async def submit_task(self, task_id: str, data: Any) -> str:
        """提交任务"""
        await self.task_queue.put(task_id, data)
        return task_id
        
    async def _process_tasks(self):
        """处理任务"""
        while self.state == EngineState.RUNNING:
            try:
                task_id, data = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )
                
                # 处理任务
                result = await self._execute_task(task_id, data)
                self.task_queue.mark_done(task_id, result)
                
                # 发布事件
                await self.event_bus.publish("task_completed", result)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Task processing error: {e}")
                
    async def _execute_task(self, task_id: str, data: Any) -> TaskResult:
        """执行任务"""
        start_time = datetime.now()
        
        try:
            # 简单任务执行
            result = data.get("action", lambda: "noop")()
            
            return TaskResult(
                task_id=task_id,
                status="completed",
                result=result,
                duration=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            return TaskResult(
                task_id=task_id,
                status="failed",
                error=str(e),
                duration=(datetime.now() - start_time).total_seconds()
            )
            
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "state": self.state.value,
            "plugins": len(self.plugins),
            "uptime": (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }
