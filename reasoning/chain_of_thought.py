"""Chain of Thought Reasoning - 思维链推理模块

提供多种推理增强策略：
- ReAct: Reasoning + Acting 模式
- Tree of Thoughts: 思维树搜索
- Self-Consistency: 自洽性聚合
- Reflexion: 反思机制
"""
import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict
import aiohttp


class ReasoningType(Enum):
    """推理类型枚举"""
    LINEAR = "linear"           # 线性推理
    BRANCHED = "branched"       # 分支推理
    TREE = "tree"              # 树状推理
    REFLEXIVE = "reflexive"    # 反思推理


class ThoughtStatus(Enum):
    """思考状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PRUNED = "pruned"
    FAILED = "failed"


@dataclass
class ReasoningStep:
    """单个推理步骤"""
    step_id: str
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    result: Optional[str] = None
    confidence: float = 0.0
    depth: int = 0
    parent_id: Optional[str] = None
    status: ThoughtStatus = ThoughtStatus.PENDING
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "step_id": self.step_id,
            "thought": self.thought,
            "action": self.action,
            "observation": self.observation,
            "result": self.result,
            "confidence": self.confidence,
            "depth": self.depth,
            "parent_id": self.parent_id,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


@dataclass
class ThoughtChain:
    """思维链"""
    chain_id: str
    problem: str
    reasoning_type: ReasoningType = ReasoningType.LINEAR
    steps: List[ ReasoningStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    overall_confidence: float = 0.0
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: ReasoningStep):
        """添加推理步骤"""
        self.steps.append(step)
    
    def get_step(self, step_id: str) -> Optional[ ReasoningStep]:
        """获取步骤"""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_path(self) -> List[ ReasoningStep]:
        """获取完整路径"""
        if not self.steps:
            return []
        
        # 按深度排序
        sorted_steps = sorted(self.steps, key=lambda x: x.depth)
        
        # 构建路径
        path = []
        current = sorted_steps[-1]  # 从最后一个步骤开始
        
        while current:
            path.insert(0, current)
            if current.parent_id:
                current = self.get_step(current.parent_id)
            else:
                break
                
        return path
    
    def calculate_confidence(self) -> float:
        """计算整体置信度"""
        if not self.steps:
            return 0.0
        
        confidences = [s.confidence for s in self.steps if s.confidence > 0]
        if not confidences:
            return 0.0
        
        return sum(confidences) / len(confidences)
    
    def export(self) -> Dict:
        """导出思维链"""
        return {
            "chain_id": self.chain_id,
            "problem": self.problem,
            "reasoning_type": self.reasoning_type.value,
            "steps": [s.to_dict() for s in self.steps],
            "final_answer": self.final_answer,
            "overall_confidence": self.overall_confidence,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }
    
    def visualize(self) -> str:
        """可视化思维链"""
        lines = [f"# Chain: {self.chain_id}"]
        lines.append(f"Problem: {self.problem}")
        lines.append(f"Type: {self.reasoning_type.value}")
        lines.append("")
        
        for step in self.steps:
            indent = "  " * step.depth
            status_icon = {
                ThoughtStatus.PENDING: "○",
                ThoughtStatus.IN_PROGRESS: "◐",
                ThoughtStatus.COMPLETED: "●",
                ThoughtStatus.PRUNED: "✗",
                ThoughtStatus.FAILED: "⚠"
            }.get(step.status, "?")
            
            lines.append(f"{indent}{status_icon} Step {step.step_id}")
            lines.append(f"{indent}  Thought: {step.thought[:80]}...")
            
            if step.action:
                lines.append(f"{indent}  Action: {step.action}")
            if step.observation:
                lines.append(f"{indent}  Observation: {step.observation[:80]}...")
            if step.result:
                lines.append(f"{indent}  Result: {step.result[:80]}...")
            lines.append(f"{indent}  Confidence: {step.confidence:.2f}")
            lines.append("")
        
        if self.final_answer:
            lines.append(f"Final Answer: {self.final_answer}")
            lines.append(f"Overall Confidence: {self.overall_confidence:.2f}")
        
        return "\n".join(lines)


class OllamaReasoner:
    """基于Ollama的推理器"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen3:8b"):
        self.base_url = base_url
        self.model = model
        self.system_prompt = """You are a reasoning expert. Break down complex problems into step-by-step thoughts.
For each thought:
1. Think carefully about what you know and what you need to find out
2. Decide on an action to gain more information or make progress
3. Observe the result of your action
4. Repeat until you reach a conclusion

Use the format:
Thought: <your reasoning>
Action: <what you do>
Observation: <what you see>
... (repeat)
Answer: <final answer>"""
    
    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """生成响应"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "top_p": 0.9,
                "num_ctx": 4096
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "")
        except Exception as e:
            print(f"Error generating: {e}")
        
        return ""
    
    async def chat(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """对话"""
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("message", {}).get("content", "")
        except Exception as e:
            print(f"Error in chat: {e}")
        
        return ""


class ReActReasoner(ReasoningType):
    """ReAct推理器 - Reasoning + Acting"""
    
    def __init__(self, reasoner: OllamaReasoner, max_steps: int = 10):
        self.reasoner = reasoner
        self.max_steps = max_steps
        self.tools: Dict[str, Callable] = {}
    
    def register_tool(self, name: str, func: Callable):
        """注册工具"""
        self.tools[name] = func
    
    async def solve(self, problem: str) -> ThoughtChain:
        """解决问题"""
        chain = ThoughtChain(
            chain_id=f"react_{int(time.time())}",
            problem=problem,
            reasoning_type=ReasoningType.LINEAR
        )
        
        context = f"Problem: {problem}\n\n"
        step_num = 0
        
        while step_num < self.max_steps:
            step_num += 1
            step_id = f"step_{step_num}"
            
            # 生成思考
            prompt = context + "\n" + self.reasoner.system_prompt + "\n\nContinue reasoning:"
            thought = await self.reasoner.generate(prompt)
            
            # 解析行动
            action = None
            observation = None
            
            for line in thought.split("\n"):
                if line.startswith("Action:"):
                    action = line.replace("Action:", "").strip()
                elif line.startswith("Observation:"):
                    observation = line.replace("Observation:", "").strip()
                elif line.startswith("Answer:"):
                    # 找到答案
                    answer = line.replace("Answer:", "").strip()
                    chain.final_answer = answer
                    chain.completed_at = time.time()
                    chain.overall_confidence = chain.calculate_confidence()
                    return chain
            
            # 执行行动
            if action and action in self.tools:
                try:
                    result = await self.tools[action]() if asyncio.iscoroutinefunction(self.tools[action]) else self.tools[action]()
                    observation = str(result)
                except Exception as e:
                    observation = f"Error: {str(e)}"
            
            # 创建步骤
            step = ReasoningStep(
                step_id=step_id,
                thought=thought,
                action=action,
                observation=observation,
                depth=step_num - 1,
                status=ThoughtStatus.COMPLETED,
                confidence=0.8
            )
            
            chain.add_step(step)
            context += f"\n{thought}\n"
            
            if observation:
                context += f"Observation: {observation}\n"
        
        chain.overall_confidence = chain.calculate_confidence()
        return chain


class TreeOfThoughts:
    """思维树推理"""
    
    def __init__(self, reasoner: OllamaReasoner, max_branches: int = 3, max_depth: int = 5):
        self.reasoner = reasoner
        self.max_branches = max_branches
        self.max_depth = max_depth
    
    async def solve(self, problem: str, evaluation_fn: Optional[Callable] = None) -> ThoughtChain:
        """解决问题"""
        # 初始化根节点
        root = ReasoningStep(
            step_id="root",
            thought=f"Initial problem: {problem}",
            depth=0,
            status=ThoughtStatus.COMPLETED
        )
        
        # 广度优先搜索
        queue = [(root, 0)]
        all_steps = [root]
        best_path = [root]
        best_score = 0.0
        
        while queue:
            current_step, depth = queue.pop(0)
            
            if depth >= self.max_depth:
                continue
            
            # 生成多个分支
            branches = await self._generate_branches(current_step, problem)
            
            for i, branch_thought in enumerate(branches):
                branch_step = ReasoningStep(
                    step_id=f"depth_{depth}_branch_{i}",
                    thought=branch_thought,
                    parent_id=current_step.step_id,
                    depth=depth + 1,
                    status=ThoughtStatus.COMPLETED
                )
                
                # 评估分支
                if evaluation_fn:
                    branch_step.confidence = await evaluation_fn(branch_thought)
                else:
                    branch_step.confidence = 0.7
                
                all_steps.append(branch_step)
                
                if branch_step.confidence > best_score:
                    best_score = branch_step.confidence
                    # 重建最佳路径
                    best_path = self._reconstruct_path(all_steps, branch_step)
                
                if depth + 1 < self.max_depth:
                    queue.append((branch_step, depth + 1))
        
        # 创建思维链
        chain = ThoughtChain(
            chain_id=f"tot_{int(time.time())}",
            problem=problem,
            reasoning_type=ReasoningType.TREE,
            steps=all_steps
        )
        
        # 设置最终答案（从最佳路径提取）
        if best_path:
            chain.final_answer = best_path[-1].thought
            chain.overall_confidence = best_score
        
        return chain
    
    async def _generate_branches(self, current_step: ReasoningStep, problem: str) -> List[str]:
        """生成多个分支"""
        prompt = f"""Given the current thought: {current_step.thought}
        
Generate {self.max_branches} different approaches or next steps to solve this problem.
Be creative and explore different angles.

Format (one per line):
1. <first approach>
2. <second approach>
3. ..."""
        
        response = await self.reasoner.generate(prompt, temperature=0.9)
        
        branches = []
        for line in response.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # 清理格式
                clean_line = line.lstrip("0123456789.-) ").strip()
                if clean_line:
                    branches.append(clean_line)
        
        return branches[:self.max_branches]
    
    def _reconstruct_path(self, all_steps: List[ ReasoningStep], target: ReasoningStep) -> List[ ReasoningStep]:
        """重建路径"""
        path = []
        current = target
        
        while current:
            path.insert(0, current)
            if current.parent_id:
                current = next((s for s in all_steps if s.step_id == current.parent_id), None)
            else:
                break
        
        return path


class SelfConsistency:
    """自洽性推理 - 聚合多条推理路径"""
    
    def __init__(self, reasoner: OllamaReasoner, num_paths: int = 5):
        self.reasoner = reasoner
        self.num_paths = num_paths
    
    async def solve(self, problem: str) -> ThoughtChain:
        """解决问题"""
        chains = []
        
        # 生成多条推理路径
        tasks = [
            self._generate_path(problem, temperature)
            for temperature in [0.3, 0.5, 0.7, 0.9, 1.0][:self.num_paths]
        ]
        
        chains = await asyncio.gather(*tasks)
        
        # 聚合结果
        answers = [chain.final_answer for chain in chains if chain.final_answer]
        
        # 投票选择最佳答案
        final_answer = self._vote(answers)
        
        # 创建聚合链
        best_chain = chains[0]
        for chain in chains:
            if chain.final_answer == final_answer:
                best_chain = chain
                break
        
        # 合并所有步骤
        merged_steps = []
        for i, chain in enumerate(chains):
            for step in chain.steps:
                step.step_id = f"path{i}_{step.step_id}"
                merged_steps.append(step)
        
        # 创建最终链
        final_chain = ThoughtChain(
            chain_id=f"sc_{int(time.time())}",
            problem=problem,
            reasoning_type=ReasoningType.BRANCHED,
            steps=merged_steps,
            final_answer=final_answer,
            overall_confidence=len([a for a in answers if a == final_answer]) / len(answers) if answers else 0.0
        )
        
        return final_chain
    
    async def _generate_path(self, problem: str, temperature: float) -> ThoughtChain:
        """生成单条路径"""
        prompt = f"""Solve this problem step by step with thorough reasoning:

{problem}

Show your complete reasoning process, then provide your final answer."""

        response = await self.reasoner.generate(prompt, temperature=temperature)
        
        chain = ThoughtChain(
            chain_id=f"path_{int(time.time())}_{temperature}",
            problem=problem,
            reasoning_type=ReasoningType.LINEAR
        )
        
        # 解析步骤
        lines = response.split("\n")
        step_id = 0
        
        for line in lines:
            if "think" in line.lower() or "reason" in line.lower():
                step_id += 1
                step = ReasoningStep(
                    step_id=f"step_{step_id}",
                    thought=line.strip(),
                    depth=step_id - 1,
                    status=ThoughtStatus.COMPLETED,
                    confidence=0.8
                )
                chain.add_step(step)
        
        # 提取最终答案（最后几行）
        answer_lines = [l for l in lines if l.strip() and not l.startswith("think")]
        if answer_lines:
            chain.final_answer = " ".join(answer_lines[-3:])
        
        return chain
    
    def _vote(self, answers: List[str]) -> str:
        """投票选择最佳答案"""
        if not answers:
            return ""
        
        # 简单投票
        counts = defaultdict(int)
        for answer in answers:
            counts[answer] += 1
        
        # 返回最高票数
        return max(counts.items(), key=lambda x: x[1])[0]


class ReflexionReasoner:
    """反思推理器"""
    
    def __init__(self, reasoner: OllamaReasoner, max_iterations: int = 3):
        self.reasoner = reasoner
        self.max_iterations = max_iterations
    
    async def solve(self, problem: str) -> ThoughtChain:
        """解决问题并反思"""
        chain = ThoughtChain(
            chain_id=f"reflex_{int(time.time())}",
            problem=problem,
            reasoning_type=ReasoningType.REFLEXIVE
        )
        
        current_attempt = 0
        best_answer = None
        best_confidence = 0.0
        
        while current_attempt < self.max_iterations:
            current_attempt += 1
            
            # 生成初始解答
            if current_attempt == 1:
                prompt = f"""Solve this problem step by step:

{problem}

Provide your complete reasoning and final answer."""
            else:
                prompt = f"""Previous attempt: {best_answer}

Problem: {problem}

Identify what was wrong or incomplete in the previous solution and provide a better answer.
Be specific about what you learned from the previous attempt."""

            response = await self.reasoner.generate(prompt, temperature=0.7)
            
            # 提取答案
            answer = self._extract_answer(response)
            
            # 评估答案
            confidence = await self._evaluate_answer(problem, answer)
            
            step = ReasoningStep(
                step_id=f"attempt_{current_attempt}",
                thought=response,
                result=answer,
                confidence=confidence,
                depth=current_attempt - 1,
                status=ThoughtStatus.COMPLETED
            )
            
            chain.add_step(step)
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_answer = answer
            
            # 如果置信度足够高，停止
            if confidence >= 0.9:
                break
        
        chain.final_answer = best_answer
        chain.overall_confidence = best_confidence
        chain.completed_at = time.time()
        
        return chain
    
    def _extract_answer(self, response: str) -> str:
        """提取答案"""
        lines = response.split("\n")
        
        # 尝试找"答案"关键词
        for i, line in enumerate(lines):
            if "answer" in line.lower() or "结论" in line:
                return " ".join(lines[i+1:i+4])
        
        # 返回最后几行
        return " ".join(lines[-3:]) if lines else response
    
    async def _evaluate_answer(self, problem: str, answer: str) -> float:
        """评估答案质量"""
        prompt = f"""Evaluate this solution to the problem:

Problem: {problem}
Solution: {answer}

Rate the quality from 0.0 to 1.0 based on:
- Correctness
- Completeness
- Clarity

Respond with ONLY a number between 0.0 and 1.0."""

        response = await self.reasoner.generate(prompt, temperature=0.3)
        
        # 提取数字
        try:
            for word in response.split():
                try:
                    score = float(word)
                    if 0 <= score <= 1:
                        return score
                except ValueError:
                    continue
        except:
            pass
        
        return 0.5  # 默认置信度


class ChainOfThoughtEngine:
    """思维链推理引擎 - 统一入口"""
    
    def __init__(self, model: str = "qwen3:8b"):
        self.reasoner = OllamaReasoner(model=model)
        self.react = ReActReasoner(self.reasoner)
        self.tree = TreeOfThoughts(self.reasoner)
        self.self_consistency = SelfConsistency(self.reasoner)
        self.reflexion = ReflexionReasoner(self.reasoner)
    
    async def solve(
        self,
        problem: str,
        method: str = "tree",
        **kwargs
    ) -> ThoughtChain:
        """解决问题
        
        Args:
            problem: 问题描述
            method: 推理方法 (react|tree|self_consistency|reflexion)
            **kwargs: 其他参数
        
        Returns:
            ThoughtChain: 思维链结果
        """
        method_map = {
            "react": self.react.solve,
            "tree": self.tree.solve,
            "self_consistency": self.self_consistency.solve,
            "reflexion": self.reflexion.solve,
            "cot": lambda p: self.tree.solve(p)  # 默认用tree
        }
        
        solver = method_map.get(method, self.tree.solve)
        return await solver(problem)
    
    async def batch_solve(
        self,
        problems: List[str],
        method: str = "tree"
    ) -> List[ThoughtChain]:
        """批量解决问题"""
        tasks = [self.solve(p, method) for p in problems]
        return await asyncio.gather(*tasks)
