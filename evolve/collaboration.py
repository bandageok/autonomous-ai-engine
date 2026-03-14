"""
Cross-Model Collaboration - 跨模型协作系统
创新点：不同LLM协同工作，每个模型发挥特长
"""
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

# ==================== 模型类型 ====================

class ModelCapability(Enum):
    REASONING = "reasoning"       # 推理能力强
    CREATIVE = "creative"        # 创意能力强
    CODING = "coding"            # 编程能力强
    ANALYSIS = "analysis"        # 分析能力强
    SUMMARY = "summary"          # 总结能力强

@dataclass
class ModelInfo:
    """模型信息"""
    name: str
    provider: str
    capabilities: List[ModelCapability]
    max_tokens: int
    cost_per_1k: float  # 美元
    latency_ms: int

# ==================== 任务路由器 ====================

class TaskRouter:
    """任务路由器 - 根据任务类型选择最佳模型"""
    
    def __init__(self):
        self.models: Dict[str, ModelInfo] = {}
        self.default_model: str = ""
        
    def register_model(self, model_id: str, info: ModelInfo):
        """注册模型"""
        self.models[model_id] = info
        
    def select_model(self, task_type: str) -> str:
        """根据任务选择模型"""
        # 任务类型到能力的映射
        capability_map = {
            "reasoning": ModelCapability.REASONING,
            "code": ModelCapability.CODING,
            "creative": ModelCapability.CREATIVE,
            "analyze": ModelCapability.ANALYSIS,
            "summary": ModelCapability.SUMMARY,
            "default": ModelCapability.REASONING
        }
        
        required_cap = capability_map.get(task_type, ModelCapability.REASONING)
        
        # 找到最合适的模型
        best_model = self.default_model
        best_score = -1
        
        for model_id, info in self.models.items():
            if required_cap in info.capabilities:
                # 计算分数：考虑能力匹配度和成本
                score = 10  # 基础分
                if required_cap in info.capabilities:
                    score += 5
                # 考虑延迟（越低越好）
                score -= info.latency_ms / 1000
                
                if score > best_score:
                    best_score = score
                    best_model = model_id
                    
        return best_model
        
    def get_model_info(self, model_id: str) -> Optional[ModelInfo]:
        """获取模型信息"""
        return self.models.get(model_id)

# ==================== 协作消息 ====================

@dataclass
class CollaborationMessage:
    """协作消息"""
    id: str
    sender: str
    receivers: List[str]
    content: Any
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

# ==================== 协作代理 ====================

class CollaborationAgent:
    """协作代理"""
    
    def __init__(self, agent_id: str, name: str, llm_provider, capabilities: List[str]):
        self.agent_id = agent_id
        self.name = name
        self.llm = llm_provider
        self.capabilities = capabilities
        self.inbox: List[CollaborationMessage] = []
        self.outbox: List[CollaborationMessage] = []
        
    async def send_to(self, receiver_id: str, content: Any, meta: Dict = None):
        """发送消息"""
        msg = CollaborationMessage(
            id=f"{self.agent_id}_{datetime.now().timestamp()}",
            sender=self.agent_id,
            receivers=[receiver_id],
            content=content,
            metadata=meta or {}
        )
        self.outbox.append(msg)
        return msg
        
    async def broadcast(self, content: Any, meta: Dict = None):
        """广播消息"""
        msg = CollaborationMessage(
            id=f"{self.agent_id}_{datetime.now().timestamp()}",
            sender=self.agent_id,
            receivers=["*"],
            content=content,
            metadata=meta or {}
        )
        self.outbox.append(msg)
        return msg
        
    async def receive(self, message: CollaborationMessage):
        """接收消息"""
        self.inbox.append(message)
        
    async def process_messages(self):
        """处理收到的消息"""
        results = []
        
        for msg in self.inbox:
            result = await self._process_message(msg)
            results.append(result)
            
        self.inbox.clear()
        return results
        
    async def _process_message(self, message: CollaborationMessage) -> Any:
        """处理单条消息"""
        # 简单实现：直接用LLM处理
        if self.llm:
            prompt = f"Process this task: {message.content}"
            return await self.llm.generate(prompt)
        return {"status": "no_llm"}

# ==================== 协作系统 ====================

class ModelCollaborationSystem:
    """跨模型协作系统"""
    
    def __init__(self):
        self.router = TaskRouter()
        self.agents: Dict[str, CollaborationAgent] = {}
        self.message_bus: List[CollaborationMessage] = []
        
    def register_agent(self, agent: CollaborationAgent):
        """注册代理"""
        self.agents[agent.agent_id] = agent
        
    def register_model(self, model_id: str, info: ModelInfo):
        """注册模型"""
        self.router.register_model(model_id, info)
        
    async def submit_task(self, task: Dict) -> Any:
        """提交任务"""
        task_type = task.get("type", "default")
        task_content = task.get("content", "")
        
        # 选择最佳模型
        model_id = self.router.select_model(task_type)
        
        # 获取模型
        agent = self.agents.get(model_id)
        if not agent:
            return {"error": f"Agent not found: {model_id}"}
            
        # 执行任务
        if agent.llm:
            result = await agent.llm.generate(task_content)
            return {"model": model_id, "result": result}
            
        return {"error": "No LLM configured"}
        
    async def collaborative_solve(self, problem: str, strategy: str = "sequential") -> Dict:
        """协作解决问题"""
        
        if strategy == "sequential":
            return await self._sequential_solve(problem)
        elif strategy == "parallel":
            return await self._parallel_solve(problem)
        elif strategy == "debate":
            return await self._debate_solve(problem)
        else:
            return {"error": f"Unknown strategy: {strategy}"}
            
    async def _sequential_solve(self, problem: str) -> Dict:
        """顺序协作：一个模型接一个"""
        results = []
        
        for agent_id, agent in self.agents.items():
            if agent.llm:
                result = await agent.llm.generate(f"Solve this step by step: {problem}\n\nPrevious context: {results}")
                results.append({
                    "agent": agent.name,
                    "result": result
                })
                
        # 汇总
        final = await self.agents.get(list(self.agents.keys())[0])
        if final and final.llm:
            summary = await final.llm.generate(
                f"Summarize these solutions into the best answer:\n{results}"
            )
            return {"strategy": "sequential", "steps": results, "final": summary}
            
        return {"strategy": "sequential", "steps": results}
        
    async def _parallel_solve(self, problem: str) -> Dict:
        """并行协作：多个模型同时解决，取最优"""
        tasks = []
        
        for agent_id, agent in self.agents.items():
            if agent.llm:
                tasks.append(self._solve_with_agent(agent, problem))
                
        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 找最佳
        valid_results = [r for r in results if not isinstance(r, Exception)]
        
        if valid_results:
            best = max(valid_results, key=lambda x: len(str(x)))
            return {"strategy": "parallel", "results": valid_results, "best": best}
            
        return {"strategy": "parallel", "error": "No valid results"}
        
    async def _solve_with_agent(self, agent: CollaborationAgent, problem: str) -> str:
        """让代理解决"""
        if agent.llm:
            return await agent.llm.generate(f"Solve: {problem}")
        return ""
        
    async def _debate_solve(self, problem: str) -> Dict:
        """辩论协作：多个模型辩论，取共识"""
        
        # 第一轮：各自提出方案
        proposals = []
        for agent_id, agent in self.agents.items():
            if agent.llm:
                proposal = await agent.llm.generate(f"Propose a solution: {problem}")
                proposals.append({"agent": agent.name, "proposal": proposal})
                
        # 第二轮：互相批评
        for i, prop1 in enumerate(proposals):
            for j, prop2 in enumerate(proposals):
                if i != j and agent.llm:
                    critique = await agent.llm.generate(
                        f"Critique this proposal: {prop1['proposal']}\n\nOther proposal: {prop2['proposal']}"
                    )
                    prop1["critique_from_other"] = critique
                    
        # 第三轮：综合
        final_agent = list(self.agents.values())[0]
        if final_agent and final_agent.llm:
            summary = await final_agent.llm.generate(
                f"Synthesize these proposals and critiques into the best solution:\n{proposals}"
            )
            return {"strategy": "debate", "proposals": proposals, "final": summary}
            
        return {"strategy": "debate", "proposals": proposals}
        
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "registered_models": len(self.models),
            "registered_agents": len(self.agents),
            "messages_in_bus": len(self.message_bus)
        }


# ==================== 使用示例 ====================

async def main():
    """使用示例"""
    
    # 创建协作系统
    system = ModelCollaborationSystem()
    
    # 注册模型（模拟）
    system.register_model("reasoner", ModelInfo(
        name="DeepThink-R1",
        provider="Ollama",
        capabilities=[ModelCapability.REASONING, ModelCapability.ANALYSIS],
        max_tokens=8000,
        cost_per_1k=0,
        latency_ms=2000
    ))
    
    system.register_model("coder", ModelInfo(
        name="CodeGen-7B", 
        provider="Ollama",
        capabilities=[ModelCapability.CODING],
        max_tokens=4000,
        cost_per_1k=0,
        latency_ms=1000
    ))
    
    system.register_model("creative", ModelInfo(
        name="Creative-AI",
        provider="Ollama",
        capabilities=[ModelCapability.CREATIVE],
        max_tokens=2000,
        cost_per_1k=0,
        latency_ms=500
    ))
    
    print("Registered models:", len(system.router.models))
    
    # 测试任务路由
    print("\nTask routing test:")
    print(f"  Coding task -> {system.router.select_model('code')}")
    print(f"  Reasoning task -> {system.router.select_model('reasoning')}")
    print(f"  Creative task -> {system.router.select_model('creative')}")
    

if __name__ == "__main__":
    asyncio.run(main())
