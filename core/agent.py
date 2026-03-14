"""Core Agent - 核心智能体"""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json

class AgentCapability(Enum):
    REASONING = "reasoning"
    PLANNING = "planning"
    TOOL_USE = "tool_use"
    LEARNING = "learning"
    COMMUNICATION = "communication"

@dataclass
class AgentConfig:
    """智能体配置"""
    name: str
    capabilities: List[AgentCapability] = field(default_factory=list)
    max_steps: int = 100
    timeout: int = 300
    memory_size: int = 1000

@dataclass
class AgentState:
    """智能体状态"""
    status: str = "idle"
    current_step: int = 0
    memory_usage: int = 0
    last_action: Optional[str] = None

class Thought:
    """思考"""
    def __init__(self, content: str, reasoning: str = ""):
        self.id = str(uuid.uuid4())
        self.content = content
        self.reasoning = reasoning
        self.timestamp = datetime.now()
        self.confidence: float = 1.0
        
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "confidence": self.confidence
        }

class Action:
    """动作"""
    def __init__(self, action_type: str, params: Dict = None):
        self.id = str(uuid.uuid4())
        self.type = action_type
        self.params = params or {}
        self.timestamp = datetime.now()
        self.result: Any = None
        self.success: bool = False
        
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "params": self.params,
            "result": str(self.result),
            "success": self.success,
            "timestamp": self.timestamp.isoformat()
        }

class Agent:
    """智能体"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState()
        self.thought_history: List[Thought] = []
        self.action_history: List[Action] = []
        self.internal_memory: Dict = {}
        
    async def think(self, prompt: str, llm_provider=None) -> Thought:
        """思考"""
        thought = Thought(content=prompt)
        
        if llm_provider:
            # 调用LLM进行推理
            reasoning = await llm_provider.generate(f"Think step by step: {prompt}")
            thought.reasoning = reasoning
            
        self.thought_history.append(thought)
        return thought
        
    async def plan(self, goal: str, steps: List[str]) -> List[Action]:
        """规划"""
        actions = []
        
        for step in steps[:self.config.max_steps]:
            action = Action(action_type="step", params={"description": step})
            actions.append(action)
            self.action_history.append(action)
            
        return actions
    
    async def execute_action(self, action: Action, executor: Callable) -> Any:
        """执行动作"""
        self.state.current_step += 1
        
        try:
            if asyncio.iscoroutinefunction(executor):
                result = await executor(action.params)
            else:
                result = executor(action.params)
                
            action.result = result
            action.success = True
            self.state.last_action = action.type
            
            return result
            
        except Exception as e:
            action.result = str(e)
            action.success = False
            raise
            
    async def learn(self, experience: Dict):
        """学习"""
        # 存储经验
        experience_id = str(uuid.uuid4())
        self.internal_memory[experience_id] = {
            **experience,
            "timestamp": datetime.now().isoformat()
        }
        
        # 简单记忆管理
        if len(self.internal_memory) > self.config.memory_size:
            # 删除最老的
            oldest = min(self.internal_memory.items(), key=lambda x: x[1]["timestamp"])
            del self.internal_memory[oldest[0]]
            
    def get_thought_history(self, last_n: int = None) -> List[Thought]:
        """获取思考历史"""
        if last_n:
            return self.thought_history[-last_n:]
        return self.thought_history
        
    def get_state(self) -> Dict:
        """获取状态"""
        return {
            "name": self.config.name,
            "status": self.state.status,
            "current_step": self.state.current_step,
            "memory_usage": len(self.internal_memory),
            "thoughts": len(self.thought_history),
            "actions": len(self.action_history)
        }
