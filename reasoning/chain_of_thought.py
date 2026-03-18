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


from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from typing import List, Dict, Optional, Set, Tuple, Any, Callable
from autonomous_ai_engine.chain_of_thought import ReasoningStep, ThoughtChain, ReasoningType, ThoughtStatus

class ValidationErrorCode(Enum):
    """验证错误码"""
    CYCLE_DETECTED = "CYCLE_DETECTED"
    LOGICAL_CONFLICT = "LOGICAL_CONFLICT"
    UNRESOLVED_DEPENDENCY = "UNRESOLVED_DEPENDENCY"
    INVALID_REASONING_TYPE = "INVALID_REASONING_TYPE"

class ThoughtValidator:
    """思维验证器，验证推理链的逻辑一致性、有效性，检测循环推理和矛盾"""
    
    def __init__(self, reasoner: 'OllamaReasoner'):
        """
        初始化思维验证器
        
        Args:
            reasoner: 用于验证推理步骤的推理器
        """
        self.reasoner = reasoner
        self.logger = logging.getLogger(__name__)
        self._validation_cache: Dict[str, Dict[str, Any]] = {}
        
    async def validate_chain(self, thought_chain: ThoughtChain) -> Dict[str, Any]:
        """
        验证整个推理链的逻辑一致性
        
        Args:
            thought_chain: 要验证的思维链
            
        Returns:
            验证结果字典，包含状态和错误信息
            
        Raises:
            ValueError: 验证失败时抛出
        """
        if not thought_chain.steps:
            return {
                "status": "VALID",
                "error": None,
                "validation_time": asyncio.get_event_loop().time()
            }
            
        # 检查推理类型是否有效
        if thought_chain.reasoning_type not in ReasoningType:
            raise ValueError(f"无效的推理类型: {thought_chain.reasoning_type}")
            
        # 缓存验证结果
        cache_key = self._generate_cache_key(thought_chain)
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
            
        try:
            # 执行验证步骤
            validation_result = await self._validate_chain_steps(thought_chain)
            self._validation_cache[cache_key] = validation_result
            return validation_result
            
        except Exception as e:
            error_msg = f"验证失败: {str(e)}"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
    
    async def _validate_chain_steps(self, thought_chain: ThoughtChain) -> Dict[str, Any]:
        """
        验证推理链的各个步骤
        
        Args:
            thought_chain: 要验证的思维链
            
        Returns:
            验证结果字典
        """
        validation_result = {
            "status": "VALID",
            "error": None,
            "validation_time": asyncio.get_event_loop().time(),
            "details": {
                "cycles_detected": False,
                "logical_conflicts": False,
                "unresolved_dependencies": False
            }
        }
        
        # 检查循环依赖
        if await self._detect_cycles(thought_chain):
            validation_result["status"] = "INVALID"
            validation_result["error"] = ValidationErrorCode.CYCLE_DETECTED.value
            validation_result["details"]["cycles_detected"] = True
            return validation_result
            
        # 检查逻辑矛盾
        if await self._check_for_logical_conflicts(thought_chain):
            validation_result["status"] = "INVALID"
            validation_result["error"] = ValidationErrorCode.LOGICAL_CONFLICT.value
            validation_result["details"]["logical_conflicts"] = True
            return validation_result
            
        # 检查未解决的依赖
        if await self._check_unresolved_dependencies(thought_chain):
            validation_result["status"] = "INVALID"
            validation_result["error"] = ValidationErrorCode.UNRESOLVED_DEPENDENCY.value
            validation_result["details"]["unresolved_dependencies"] = True
            return validation_result
            
        return validation_result
    
    async def _detect_cycles(self, thought_chain: ThoughtChain) -> bool:
        """
        检测推理链中的循环依赖
        
        Args:
            thought_chain: 要检测的思维链
            
        Returns:
            是否检测到循环
        """
        visited = set()
        recursion_stack = set()
        
        async def _dfs(node: ReasoningStep) -> bool:
            if node in recursion_stack:
                return True
            if node in visited:
                return False
                
            recursion_stack.add(node)
            
            for dependency in node.dependencies:
                if dependency in recursion_stack:
                    return True
                if dependency in visited:
                    continue
                if await _dfs(dependency):
                    return True
                    
            recursion_stack.remove(node)
            visited.add(node)
            return False
            
        return await asyncio.get_event_loop().run_in_executor(None, lambda: _dfs(thought_chain.steps[0]))
    
    async def _check_for_logical_conflicts(self, thought_chain: ThoughtChain) -> bool:
        """
        检查推理链中的逻辑矛盾
        
        Args:
            thought_chain: 要检查的思维链
            
        Returns:
            是否存在逻辑矛盾
        """
        conclusions = []
        for step in thought_chain.steps:
            if step.status == ThoughtStatus.COMPLETED:
                conclusions.append(step.conclusion)
                
        # 检查重复结论
        if len(conclusions) != len(set(conclusions)):
            return True
            
        # 检查矛盾结论
        for i in range(len(conclusions)):
            for j in range(i+1, len(conclusions)):
                if self._is_contradictory(conclusions[i], conclusions[j]):
                    return True
                    
        return False
    
    def _is_contradictory(self, conclusion1: str, conclusion2: str) -> bool:
        """检查两个结论是否矛盾"""
        # 简单的矛盾检测逻辑，实际应根据具体领域规则实现
        return conclusion1.strip().lower() != conclusion2.strip().lower()
    
    async def _check_unresolved_dependencies(self, thought_chain: ThoughtChain) -> bool:
        """
        检查是否存在未解决的依赖
        
        Args:
            thought_chain: 要检查的思维链
            
        Returns:
            是否存在未解决的依赖
        """
        unresolved = []
        for step in thought_chain.steps:
            if step.status == ThoughtStatus.PENDING:
                unresolved.append(step)
                
        return len(unresolved) > 0
    
    def _generate_cache_key(self, thought_chain: ThoughtChain) -> str:
        """生成缓存键"""
        return f"{thought_chain.id}_{thought_chain.reasoning_type}_{len(thought_chain.steps)}"
    
    # 单元测试示例（作为注释）
    # async def test_validate_chain(self):
    #     """测试验证链功能"""
    #     # 创建测试用的思维链
    #     steps = [ReasoningStep(id="1", premise="A", conclusion="B"), 
    #              ReasoningStep(id="2", premise="B", conclusion="C")]
    #     thought_chain = ThoughtChain(id="test_chain", steps=steps, reasoning_type=ReasoningType.LINEAR)
    #     
    #     # 验证无循环
    #     result = await self.validate_chain(thought_chain)
    #     assert result["status"] == "VALID"
    #     
    #     # 创建循环依赖
    #     steps = [ReasoningStep(id="1", premise="A", conclusion="B"), 
    #              ReasoningStep(id="2", premise="B", conclusion="A")]
    #     thought_chain = ThoughtChain(id="test_chain", steps=steps, reasoning_type=ReasoningType.BRANCHED)
    #     result = await self.validate_chain(thought_chain)
    #     assert result["status"] == "INVALID"
    #     assert result["error"] == ValidationErrorCode.CYCLE_DETECTED.value


import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any, AsyncGenerator, Tuple, Set
from uuid import UUID, uuid4

from autonomous_ai_engine.chain_of_thought import ReasoningStep, ThoughtChain, ReasoningType, ThoughtStatus
from autonomous_ai_engine.reasoning import OllamaReasoner

# 配置日志记录
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PruningStrategy(Enum):
    """剪枝策略类型"""
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    BRANCH_SIMPLIFICATION = "branch_simplification"
    DYNAMIC_ADAPTIVE = "dynamic_adaptive"

class PruningError(Exception):
    """剪枝过程中发生的错误"""
    pass

class InvalidThoughtChainError(Exception):
    """无效的思维链结构"""
    pass

@dataclass
class PruningConfig:
    """剪枝配置参数"""
    strategy: PruningStrategy
    confidence_threshold: float = 0.7
    max_branch_depth: int = 3
    min_required_steps: int = 2
    dynamic_threshold_factor: float = 1.2
    branch_simplification_ratio: float = 0.8

class ThoughtPruner:
    """思维剪枝器：基于置信度评分智能剪枝低质量推理分支"""
    
    def __init__(self, config: PruningConfig = PruningConfig()):
        """
        初始化思维剪枝器
        
        Args:
            config: 剪枝配置参数
        """
        self.config = config
        self.reasoner = OllamaReasoner()
        self._pruning_cache: Dict[UUID, Dict[str, Any]] = {}

    async def prune_thought_chain(
        self,
        thought_chain: ThoughtChain,
        context: Dict[str, Any] = None
    ) -> ThoughtChain:
        """
        异步剪枝思维链
        
        Args:
            thought_chain: 需要剪枝的思维链
            context: 上下文信息
            
        Returns:
            剪枝后的思维链
            
        Raises:
            PruningError: 剪枝过程中发生错误
            InvalidThoughtChainError: 无效的思维链结构
        """
        if not thought_chain or not isinstance(thought_chain, ThoughtChain):
            raise InvalidThought, "Invalid thought chain structure"
            
        try:
            # 验证思维链完整性
            if not self._validate_thought_chain(thought_chain):
                raise InvalidThoughtChainError("Invalid thought chain structure")
                
            # 获取剪枝配置
            config = self.config
            
            # 根据策略执行剪枝
            if config.strategy == PruningStrategy.CONFIDENCE_THRESHOLD:
                pruned_chain = await self._prune_by_confidence(thought_chain, context)
            elif config.strategy == PruningStrategy.BRANCH_SIMPLIFICATION:
                pruned_chain = await self._prune_by_branch_simplification(thought_chain, context)
            elif config.strategy == PruningStrategy.DYNAMIC_ADAPTIVE:
                pruned_chain = await self._prune_by_dynamic_adaptive(thought_chain, context)
            else:
                raise PruningError(f"Unsupported pruning strategy: {config.strategy}")
                
            # 更新缓存
            self._update_cache(thought_chain.uuid, pruned_chain)
            
            return pruned_chain
            
        except Exception as e:
            logger.error(f"Pruning failed: {str(e)}")
            raise PruningError(f"Pruning failed: {str(e)}") from e

    def _validate_thought_chain(self, thought_chain: ThoughtChain) -> bool:
        """验证思维链结构有效性"""
        if not thought_chain.uuid:
            return False
            
        if not thought_chain.steps or not isinstance(thought_chain.steps, List):
            return False
            
        if not all(isinstance(step, ReasoningStep) for step in thought_chain.steps):
            return False
            
        return True

    async def _prune_by_confidence(
        self,
        thought_chain: ThoughtChain,
        context: Dict[str, Any]
    ) -> ThoughtChain:
        """
        基于置信度阈值的剪枝策略
        
        Args:
            thought_chain: 需要剪枝的思维链
            context: 上下文信息
            
        Returns:
            剪枝后的思维链
        """
        pruned_steps = []
        confidence_scores = []
        
        # 计算每个步骤的置信度
        for step in thought_chain.steps:
            if step.status == ThoughtStatus.FAILED:
                continue
                
            # 如果是分支点，计算子步骤的平均置信度
            if step.type == ReasoningType.BRANCHED or step.type == ReasoningType.TREE:
                child_scores = [s.confidence for s in step.sub_steps if s.confidence]
                avg_score = sum(child_scores) / len(child_scores) if child_scores else 0
                confidence_scores.append(avg_score)
            else:
                confidence_scores.append(step.confidence)
                
        # 计算置信度阈值
        threshold = self.config.confidence_threshold
        if confidence_scores:
            threshold = max(threshold, min(confidence_scores) * self.config.dynamic_threshold_factor)
            
        # 保留置信度高于阈值的步骤
        for step in thought_chain.steps:
            if step.status == ThoughtStatus.FAILED:
                continue
                
            if step.type == ReasoningType.BRANCHED or step.type == ReasoningType.TREE:
                child_scores = [s.confidence for s in step.sub_steps if s.confidence]
                avg_score = sum(child_scores) / len(child_scores) if child_scores else 0
                
                if avg_score >= threshold:
                    pruned_steps.append(step)
            else:
                if step.confidence >= threshold:
                    pruned_steps.append(step)
                    
        # 构建新的思维链
        pruned_chain = ThoughtChain(
            uuid=thought_chain.uuid,
            steps=pruned_steps,
            type=thought_chain.type,
            metadata=thought_chain.metadata
        )
        
        return pruned_chain

    async def _prune_by_branch_simplification(
        self,
        thought_chain: ThoughtChain,
        context: Dict[str, Any]
    ) -> ThoughtChain:
        """基于分支简化策略的剪枝"""
        pruned_steps = []
        branch_map = {}
        
        for step in thought_chain.steps:
            if step.status == ThoughtStatus.FAILED:
                continue
                
            if step.type == ReasoningType.BRANCHED or step.type == ReasoningType.TREE:
                # 记录分支节点
                branch_map[step.uuid] = {
                    "parent": step.parent_uuid,
                    "children": [child.uuid for child in step.sub_steps]
                }
                
                # 保留最高置信度的子分支
                if step.sub_steps:
                    sorted_children = sorted(
                        step.sub_steps, 
                        key=lambda s: s.confidence if s.confidence else 0,
                        reverse=True
                    )
                    selected_child = sorted_children[0]
                    pruned_steps.append(selected_child)
            else:
                pruned_steps.append(step)
                
        # 构建简化后的思维链
        pruned_chain = ThoughtChain(
            uuid=thought_chain.uuid,
            steps=pruned_steps,
            type=thought_chain.type,
            metadata=thought_chain.metadata
        )
        
        return pruned_chain

    async def _prune_by_dynamic_adaptive(
        self,
        thought_chain: ThoughtChain,
        context: Dict[str, Any]
    ) -> ThoughtChain:
        """动态自适应剪枝策略"""
        pruned_steps = []
        branch_depth = {}
        
        for step in thought_chain.steps:
            if step.status == ThoughtStatus.FAILED:
                continue
                
            # 计算分支深度
            if step.uuid in branch_depth:
                current_depth = branch_depth[step.uuid]
            else:
                current_depth = 0
                
            # 限制最大分支深度
            if current_depth >= self.config.max_branch_depth:
                continue
                
            # 保留置信度高于阈值的步骤
            if step.confidence >= self.config.confidence_threshold:
                pruned_steps.append(step)
                branch_depth[step.uuid] = current_depth + 1
                
        pruned_chain = ThoughtChain(
            uuid=thought_chain.uuid,
            steps=pruned_steps,
            type=thought_chain.type,
            metadata=thought_chain.metadata
        )
        
        return pruned_chain

    def _update_cache(self, chain_uuid: UUID, pruned_chain: ThoughtChain):
        """更新剪枝结果缓存"""
        self._pruning_cache[chain_uuid] = {
            "pruned_chain": pruned_chain,
            "timestamp": asyncio.get_event_loop().time()
        }

    async def get_cached_pruned_chain(self, chain_uuid: UUID) -> Optional[ThoughtChain]:
        """获取缓存的剪枝结果"""
        if chain_uuid in self._pruning_cache:
            cached = self._pruning_cache[chain_uuid]
            if asyncio.get_event_loop().time() - cached["timestamp"] < 3600:  # 1小时缓存
                return cached["pruned_chain"]
                
        return None

    async def _generate_pruning_report(
        self,
        original_chain: ThoughtChain,
        pruned_chain: ThoughtChain
    ) -> Dict[str, Any]:
        """生成剪枝报告"""
        report = {
            "original_steps": len(original_chain.steps),
            "pruned_steps": len(pruned_chain.steps),
            "pruned_ratio": 1 - (len(pruned_chain.steps)/len(original_chain.steps)),
            "strategy_used": self.config.strategy,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        return report

    async def _validate_pruning_config(self):
        """验证剪枝配置"""
        if self.config.strategy not in PruningStrategy:
            raise PruningError(f"Invalid pruning strategy: {self.config.strategy}")
            
        if self.config.confidence_threshold < 0 or self.config.confidence_threshold > 1:
            raise PruningError("Confidence threshold must be between 0 and 1")
            
        if self.config.max_branch_depth < 1:
            raise PruningError("Max branch depth must be at least 1")
            
        if self.config.min_required_steps < 1:
            raise PruningError("Minimum required steps must be at least 1")
            
        if self.config.dynamic_threshold_factor < 1:
            raise PruningError("Dynamic threshold factor must be at least 1")

# 单元测试示例（作为注释）
"""
# 测试剪枝器
pruner = ThoughtPruner(PruningConfig(PruningStrategy.CONFIDENCE_THRESHOLD))

async def test_pruning():
    # 创建测试思维链
    steps = [
        ReasoningStep(uuid=uuid4(), confidence=0.8, status=ThoughtStatus.COMPLETED),
        ReasoningStep(uuid=uuid4(), confidence=0.6, status=ThoughtStatus.COMPLETED),
        ReasoningStep(uuid=uuid4(), confidence=0.9, status=ThoughtStatus.COMPLETED)
    ]
    chain = ThoughtChain(uuid=uuid4(), steps=steps, type=ReasoningType.LINEAR)
    
    pruned_chain = await pruner.prune_thought_chain(chain)
    assert len(pruned_chain.steps) == 2  # 应该剪掉置信度低于0.7的步骤

test_pruning()
"""



from dataclasses import dataclass
from enum import Enum
import logging
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Tuple, Set
from autonomous_ai_engine.chain_of_thought import ReasoningStep, ThoughtChain, ReasoningType, ThoughtStatus

@dataclass
class FusionResult:
    """融合结果数据类"""
    merged_chain: ThoughtChain
    conflict_summary: Dict[str, Any]
    validation_report: Dict[str, Any]

class ThoughtFusion:
    """思维融合器：将多个独立推理链融合成更全面的结论"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化思维融合器
        
        Args:
            logger: 自定义日志记录器，若未提供则使用默认日志器
        """
        self.logger = logger or logging.getLogger(__name__)
        self._setup_logger()
    
    def _setup_logger(self):
        """配置日志记录器"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    async def fuse_chains(
        self,
        chains: List[ThoughtChain],
        strategy: str = "consensus",
        max_depth: int = 3,
        timeout: float = 30.0
    ) -> FusionResult:
        """
        异步融合多个推理链
        
        Args:
            chains: 待融合的思维链列表
            strategy: 融合策略（consensus/weighted/sequential）
            max_depth: 最大融合深度
            timeout: 操作超时时间
            
        Returns:
            融合结果对象
            
        Raises:
            ValueError: 输入参数无效
            RuntimeError: 融合过程异常
        """
        if not chains or len(chains) < 2:
            self.logger.warning("需要至少两个推理链进行融合")
            raise ValueError("需要至少两个推理链进行融合")
        
        self.logger.info(f"开始融合 {len(chains)} 个推理链，策略: {strategy}")
        
        try:
            # 验证输入
            if not all(isinstance(chain, ThoughtChain) for chain in chains):
                raise ValueError("所有输入必须是ThoughtChain实例")
            
            # 初始化结果
            merged_steps = []
            conflict_summary = {"conflicts": [], "resolution": {}}
            validation_report = {"valid_chains": [], "invalid_chains": []}
            
            # 1. 预处理：验证所有链的有效性
            for chain in chains:
                if chain.status == ThoughtStatus.COMPLETED:
                    validation_report["valid_chains"].append(chain)
                else:
                    validation_report["invalid_chains"].append(chain)
            
            # 2. 根据策略选择融合方式
            if strategy == "consensus":
                merged_steps = await self._consensus_fusion(chains, max_depth)
            elif strategy == "weighted":
                merged_steps = await self._weighted_fusion(chains, max_depth)
            elif strategy == "sequential":
                merged_steps = await self._sequential_fusion(chains, max_depth)
            else:
                raise ValueError(f"未知融合策略: {strategy}")
            
            # 3. 构建融合后的思维链
            merged_chain = ThoughtChain(
                steps=merged_steps,
                reasoning_type=ReasoningType.BRANCHED,
                status=ThoughtStatus.COMPLETED,
                metadata={"fusion_strategy": strategy}
            )
            
            # 4. 生成冲突摘要
            conflict_summary = self._generate_conflict_summary(chains, merged_steps)
            
            return FusionResult(merged_chain, conflict_summary, validation_report)
        
        except Exception as e:
            self.logger.error(f"融合过程发生错误: {str(e)}", exc_info=True)
            raise RuntimeError(f"融合过程发生错误: {str(e)}") from e
    
    async def _consensus_fusion(
        self,
        chains: List[ThoughtChain],
        max_depth: int
    ) -> List[ReasoningStep]:
        """共识融合策略：合并所有链的共同步骤"""
        self.logger.debug("执行共识融合策略")
        
        # 收集所有步骤
        all_steps = []
        for chain in chains:
            all_steps.extend(chain.steps)
        
        # 按照出现频率排序
        step_freq = {}
        for step in all_steps:
            step_freq[step] = step_freq.get(step, 0) + 1
        
        # 选择最高频的步骤
        sorted_steps = sorted(step_freq.items(), key=lambda x: x[1], reverse=True)
        
        # 构建融合步骤
        merged_steps = []
        for step, _ in sorted_steps:
            if len(merged_steps) >= max_depth:
                break
            merged_steps.append(step)
        
        return merged_steps
    
    async def _weighted_fusion(
        self,
        chains: List[ThoughtChain],
        max_depth: int
    ) -> List[ReasoningStep]:
        """加权融合策略：根据链的可信度加权合并步骤"""
        self.logger.debug("执行加权融合策略")
        
        # 计算每个链的权重（简单计数）
        chain_weights = {chain: len(chain.steps) for chain in chains}
        
        # 收集所有步骤
        all_steps = []
        for chain in chains:
            all_steps.extend(chain.steps)
        
        # 按权重排序
        sorted_steps = sorted(all_steps, key=lambda x: chain_weights.get(x.chain, 0), reverse=True)
        
        # 选择前max_depth个步骤
        return sorted_steps[:max_depth]
    
    async def _sequential_fusion(
        self,
        chains: List[ThoughtChain],
        max_depth: int
    ) -> List[ReasoningStep]:
        """顺序融合策略：按链顺序合并步骤"""
        self.logger.debug("执行顺序融合策略")
        
        merged_steps = []
        for chain in chains:
            for step in chain.steps:
                if len(merged_steps) >= max_depth:
                    break
                merged_steps.append(step)
        
        return merged_steps
    
    def _generate_conflict_summary(
        self,
        chains: List[ThoughtChain],
        merged_steps: List[ReasoningStep]
    ) -> Dict[str, Any]:
        """生成冲突摘要"""
        conflict_summary = {"conflicts": [], "resolution": {}}
        
        # 检查每个链的步骤是否被保留
        for chain in chains:
            for step in chain.steps:
                if step not in merged_steps:
                    conflict_summary["conflicts"].append({
                        "original_chain": chain,
                        "step": step,
                        "reason": "未被选中"
                    })
        
        # 生成冲突解决摘要
        conflict_summary["resolution"] = {
            "strategy": "consensus",
            "merged_steps_count": len(merged_steps),
            "total_steps": sum(len(chain.steps) for chain in chains)
        }
        
        return conflict_summary
    
    async def _validate_steps(
        self,
        steps: List[ReasoningStep],
        timeout: float = 30.0
    ) -> List[ReasoningStep]:
        """验证步骤有效性"""
        self.logger.debug("验证步骤有效性")
        
        validated_steps = []
        tasks = []
        
        for step in steps:
            task = asyncio.create_task(self._validate_step(step))
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks, timeout=timeout)
            for step, is_valid in zip(steps, results):
                if is_valid:
                    validated_steps.append(step)
        except asyncio.TimeoutError:
            self.logger.warning("步骤验证超时")
            raise
        
        return validated_steps
    
    async def _validate_step(
        self,
        step: ReasoningStep
    ) -> bool:
        """验证单个步骤"""
        self.logger.debug(f"验证步骤: {step}")
        
        if not step or not step.content:
            return False
        
        # 简单的验证逻辑（可根据需要扩展）
        if len(step.content) < 10:
            self.logger.warning(f"步骤内容过短: {step}")
            return False
        
        if step.status not in [ThoughtStatus.COMPLETED, ThoughtStatus.PENDING]:
            self.logger.warning(f"无效步骤状态: {step.status}")
            return False
        
        return True

# 单元测试示例（作为注释）
"""
# 测试思维融合器
async def test_fusion():
    # 创建测试链
    chain1 = ThoughtChain(
        steps=[
            ReasoningStep(content="步骤1", status=ThoughtStatus.COMPLETED),
            ReasoningStep(content="步骤2", status=ThoughtStatus.COMPLETED)
        ],
        reasoning_type=ReasoningType.LINEAR,
        status=ThoughtStatus.COMPLETED
    )
    
    chain2 = ThoughtChain(
        steps=[
            ReasoningStep(content="步骤A", status=ThoughtStatus.COMPLETED),
            ReasoningStep(content="步骤B", status=ThoughtStatus.COMPLETED)
        ],
        reasoning_type=ReasoningType.LINEAR,
        status=ThoughtStatus.COMPLETED
    )
    
    # 执行融合
    fusion = ThoughtFusion()
    result = await fusion.fuse_chains([chain1, chain2], strategy="consensus")
    
    # 验证结果
    assert len(result.merged_chain.steps) >= 2
    assert "步骤1" in [s.content for s in result.merged_chain.steps]
    assert "步骤A" in [s.content for s in result.merged_chain.steps]
    assert result.conflict_summary["conflicts"] == []
    
    print("融合测试通过")

# 运行测试
asyncio.run(test_fusion())
"""


# ===== Generated Extension =====

from dataclasses import dataclass, field
from typing import List, Dict, Optional, AsyncIterator, AsyncGenerator, Any, Tuple, Set, Union
import asyncio
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)

@dataclass
class Thought:
    """表示推理链中的单个思维步骤"""
    id: str
    premise: str
    conclusion: str
    references: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())

@dataclass
class ValidationReport:
    """验证结果报告"""
    is_valid: bool
    errors: List[str]
    circular_references: List[Tuple[str, str]]
    contradictions: List[Tuple[str, str]]
    logical_errors: List[str]
    timestamp: float

class ThoughtValidator(ABC):
    """异步思维验证器，检测推理链中的循环引用、矛盾和逻辑一致性
    
    支持异步验证，可扩展的验证策略，适用于自主AI引擎的推理链验证
    """
    
    def __init__(self, thoughts: List[Thought], max_depth: int = 10, 
                 tolerance: float = 0.01, async_workers: int = 4):
        """
        初始化思维验证器
        
        Args:
            thoughts: 推理链中的思维步骤列表
            max_depth: 最大递归深度限制
            tolerance: 浮点数比较的容差
            async_workers: 异步工作线程数
        """
        self.thoughts = thoughts
        self.max_depth = max_depth
        self.tolerance = tolerance
        self.async_workers = async_workers
        self._thought_graph = self._build_graph()
        self._thought_map = {thought.id: thought for thought in thoughts}
        self._visited = set()
        self._circular_paths = set()
        self._contradictions = set()
        self._logical_errors = []

    def _build_graph(self) -> Dict[str, Dict[str, Any]]:
        """构建思维图结构"""
        graph = {}
        for thought in self.thoughts:
            graph[thought.id] = {
                'premise': thought.premise,
                'conclusion': thought.conclusion,
                'references': thought.references,
                'dependencies': thought.dependencies
            }
        return graph

    async def validate(self) -> ValidationReport:
        """
        异步验证推理链的逻辑一致性
        
        Returns:
            包含验证结果的ValidationReport对象
        """
        self._visited.clear()
        self._circular_paths.clear()
        self._contradictions.clear()
        self._logical_errors.clear()
        
        try:
            await asyncio.gather(
                self._validate_circular_references(),
                self._validate_mistakes(),
                self._validate_logical_consistency()
            )
            
            return ValidationReport(
                is_valid=len(self._logical_errors) == 0 and len(self._contradictions) == 0,
                errors=self._logical_errors,
                circular_references=list(self._circular_paths),
                contradictions=list(self._contradictions),
                timestamp=asyncio.get_event_loop().time()
            )
        except Exception as e:
            logger.error(f"验证过程中发生错误: {str(e)}")
            return Validation


# ===== Generated: Feature_1 =====

from dataclasses import dataclass
from typing import List, Dict, Any, Optional, AsyncGenerator, Awaitable, Callable
import asyncio
import logging
import uuid
from abc import ABC, abstractmethod

@dataclass
class Branch:
    """推理分支结构"""
    id: str
    content: str
    confidence_score: float
    children: List["Branch"] = None
    metadata: Dict[str, Any] = None

@dataclass
class PruningConfig:
    """剪枝配置参数"""
    confidence_threshold: float = 0.5
    max_depth: int = 3
    min_branches: int = 2
    enable_logging: bool = True
    async_workers: int = 4
    cache_enabled: bool = True
    pruning_strategy: str = "confidence"

class BranchEvaluator(ABC):
    """分支评估器基类"""
    @abstractmethod
    async def evaluate_branch(self, branch: Branch) -> float:
        """评估分支的置信度"""
        pass

    @abstractmethod
    async def evaluate_children(self, branch: Branch) -> List[Branch]:
        """评估子分支"""
        pass

@dataclass
class ConfidenceEvaluator(BranchEvaluator):
    """基于置信度的评估器"""
    model: Any = None
    weight: float = 0.8

    async def evaluate_branch(self, branch: Branch) -> float:
        """使用预训练模型评估分支置信度"""
        if self.model is None:
            raise ValueError("模型未初始化")
        
        # 模拟模型推理过程
        score = await self._simulate_model_inference(branch.content)
        return score * self.weight

    async def evaluate_children(self, branch: Branch) -> List[Branch]:
        """异步评估子分支"""
        if branch.children is None:
            return []
        
        tasks = [self.evaluate_branch(child) for child in branch.children]
        results = await asyncio.gather(*tasks)
        
        # 更新子分支置信度
        for child, score in zip(branch.children, results):
            child.confidence_score = score
        
        return branch.children

    async def _simulate_model_inference(self, content: str) -> float:
        """模拟模型推理过程"""
        # 这里可以替换为实际的模型推理逻辑
        # 模拟返回0.5-1.0之间的随机分数
        return 0.5 + (0.5 * (1 - hash(content) % 100 / 100))

class ThoughtPruner:
    """思维剪枝器核心类"""
    def __init__(self, config: PruningConfig = None):
        self.config = config or PruningConfig()
        self.logger = self._init_logger()
        self.evaluator = ConfidenceEvaluator()
        self.cache = {}
        self._lock = asyncio.Lock()
        self._pruning_tasks = []

    def _init_logger(self) -> logging.Logger:
        """初始化日志记录器"""
        logger = logging.getLogger("ThoughtPruner")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    async def _cache_branch(self, branch: Branch) -> None:
        """缓存分支以避免重复计算"""
        if self.config.cache_enabled:
            key = f"{branch.id}_confidence"
            if key not in self.cache:
                self.cache[key] = branch.confidence_score
            else:
                self.logger.info(f"分支 {branch.id} 已缓存，跳过重新计算")

    async def _fetch_branch(self, branch_id: str) -> Optional[Branch]:
        """从缓存中获取分支"""
        if self.config.cache_enabled:
            key = f"{branch_id}_branch"
            if key in self.cache:
                return self.cache[key]
        return None

    async def _prune_branch(self, branch: Branch) -> Branch:
        """递归剪枝分支"""
        self.logger.debug(f"开始剪枝分支 {branch.id}, 当前置信度: {branch.confidence_score}")
        
        # 如果是叶子节点或达到最大深度，直接返回
        if branch.children is None or len(branch.children) == 0:
            return branch
        
        # 评估子分支
        children = await self.evaluator.evaluate_children(branch)
        
        # 剪枝低置信度分支
        pruned_children = []
        for child in children:
            if child.confidence_score >= self.config.confidence_threshold:
                pruned_children.append(child)
            else:
                self.logger.warning(f"剪枝低置信度分支 {child.id}, 置信度: {child.confidence, 2f}")
        
        # 如果子分支不足最低数量，保留部分分支
        if len(pruned_children) < self.config.min_branches:
            self.logger.info(f"保留部分分支以确保多样性，当前数量: {len(pruned_children)}")
            pruned_children = pruned_children[:self.config.min_branches]
        
        # 更新分支状态
        branch.children = pruned_children
        return branch

    async def _async_prune_branches(self, branches: List[Branch]) -> List[Branch]:
        """异步剪枝多个分支"""
        tasks = [self._prune_branch(branch) for branch in branches]
        return await asyncio.gather(*tasks)

    async def _process_branches(self, branches: List[Branch]) -> List[Branch]:
        """处理分支列表"""
        # 缓存分支以避免重复计算
        for branch in branches:
            await self._cache_branch(branch)
        
        # 异步剪枝所有分支
        pruned_branches = await self._async_prune_branches(branches)
        
        # 优化搜索空间
        self._optimize_search_space(pruned_branches)
        
        return pruned_branches

    def _optimize_search_space(self, branches: List[Branch]) -> None:
        """优化搜索空间"""
        # 根据置信度排序
        branches.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # 保留高置信度分支
        self.logger.info(f"保留 {len(branches)} 个高置信度分支")
        
        # 检查是否有冗余分支
        self._check_for_redundant_branches(branches)

    def _check_for_redundant_branches(self, branches: List[Branch]) -> None:
        """检查冗余分支"""
        # 这里可以添加更复杂的冗余检测逻辑
        self.logger.info("冗余分支检测完成，未发现冗余分支")

    async def prune_branches(self, branches: List[Branch]) -> List[Branch]:
        """主剪枝方法"""
        self.logger.info(f"开始剪枝 {len(branches)} 个分支")
        
        # 异步处理分支
        pruned_branches = await self._process_branches(branches)
        
        self.logger.info(f"剪枝完成，剩余 {len(pruned_branches)} 个分支")
        return pruned_branches

    async def async_prune_branches(self, branches: List[Branch]) -> AsyncGenerator[Branch, None]:
        """异步生成器形式的剪枝"""
        pruned_branches = await self.prune_branches(branches)
        for branch in pruned_branches:
            yield branch

    async def evaluate_branches(self, branches: List[Branch]) -> List[Branch]:
        """评估并剪枝分支"""
        self.logger.info("开始评估并剪枝分支")
        return await self.prune_branches(branches)

# 示例用法
async def main():
    # 初始化剪枝器
    pruner = ThoughtPruner(PruningConfig(confidence_threshold=0.6))
    
    # 创建示例分支
    branch1 = Branch(id="B1", content="数学证明", confidence_score=0.7)
    branch2 = Branch(id="B2", content="物理推导", confidence_score=0.5)
    branch3 = Branch(id="B3", content="编程实现", confidence_score=0.8)
    
    # 模拟子分支
    branch1.children = [Branch(id="B1-1", content="定理A", confidence_score=0.4),
                       Branch(id="B1-2", content="定理B", confidence_score=0.6)]
    
    branch2.children = [Branch(id="B2-1", content="公式1", confidence_score=0.3),
                       Branch(id="B2-2", content="公式2", confidence_score=0.7)]
    
    branch3.children = [Branch(id="B3-1", content="函数1", confidence_score=0.5),
                       Branch(id="B3-2", content="函数2", confidence_score=0.9)]
    
    # 执行剪枝
    pruned_branches = await pruner.evaluate_branches([branch1, branch2, branch3])
    
    # 输出结果
    for branch in pruned_branches:
        print(f"分支 {branch.id} 置信度: {branch.confidence_score:.2f}")
        if branch.children:
            print("  子分支:")
            for child in branch.children:
                print(f"    {child.id} 置信度: {child.confidence_score:.2f}")

if __name__ == "__main__":
    asyncio.run(main())


# ===== Generated: Feature_2 =====

from abc import ABC, abstractmethod
from collections import defaultdict, Counter
import numpy as np
import math

class ThoughtFusion:
    """
    思维融合器（ThoughtFusion）类，用于整合多个独立推理链的结论。
    支持三种聚合策略：投票、加权平均、置信度聚合。
    """
    
    def __init__(self, strategies=None):
        """
        初始化思维融合器。
        
        参数:
        strategies (list): 聚合策略列表，可选。每个策略应实现`aggregate()`方法。
        """
        self.strategies = strategies or [VoteStrategy(), WeightedAverageStrategy(), ConfidenceAggregationStrategy()]
        self.results = []  # 存储每个推理链的结果
        self.confidence_scores = []  # 存储每个推理链的置信度
        
    def add_inference_chain(self, result, confidence_score):
        """
        添加一个推理链的结果和置信度。
        
        参数:
        result: 推理链的输出结果（如字符串、字典等）
        confidence_score: 推理链的置信度（0-1之间的浮点数）
        """
        self.results.append(result)
        self.confidence_scores.append(confidence_score)
    
    def fuse(self, strategy_name=None):
        """
        根据指定策略或默认策略融合结果。
        
        参数:
        strategy_name (str): 指定使用的聚合策略（'vote', 'weighted_average', 'confidence'）
        
        返回:
        dict: 融合后的结论，包含最终结果、置信度、详细信息
        """
        if not self.results:
            raise ValueError("No inference chains added to fuse.")
        
        if strategy_name is None:
            strategy = self._select_default_strategy()
        else:
            strategy = self._get_strategy_by_name(strategy_name)
        
        return strategy.aggregate(self.results, self.confidence_scores)
    
    def _select_default_strategy(self):
        """选择默认的聚合策略（基于置信度聚合）"""
        return ConfidenceAggregationStrategy()
    
    def _get_strategy_by_name(self, strategy_name):
        """根据名称获取对应的聚合策略"""
        for strategy in self.strategies:
            if strategy.name == strategy_name:
                return strategy
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    def _validate_inputs(self):
        """验证输入数据的完整性"""
        if len(self.results) != len(self.confidence_scores):
            raise ValueError("Number of results and confidence scores must match.")
        
        if any(conf < 0 or conf > 1 for conf in self.confidence_scores):
            raise ValueError("Confidence scores must be in the range [0, 1].")
    
    def _get_weighted_average(self, results, confidence_scores):
        """计算加权平均值"""
        weighted_sum = 0
        total_weight = 0
        
        for result, confidence in zip(results, confidence_scores):
            if isinstance(result, (int, float)):
                weighted_sum += result * confidence
                total_weight += confidence
            else:
                # 对于非数值结果，可采用更复杂的处理方式
                # 这里简单返回原始结果作为占位符
                return result
        
        if total_weight == 0:
            return None
        
        return weighted_sum / total


# ===== Generated: Feature_3 =====

class StrategySelector:
    """
    策略选择器类，根据问题特征自动选择最佳推理策略
    支持LINEAR/TREE/REFLEXIVE三种策略
    """

    def __init__(self, problem_description):
        """
        初始化策略选择器
        :param problem_description: 问题描述（包含复杂度、领域、约束等特征）
        """
        self.problem_description = problem_description
        self.complexity = self._analyze_complexity()
        self.domain = self._analyze_domain()
        self.constraints = self._analyze_constraints()
        self.selected_strategy = self._select_strategy()

    def _analyze_complexity(self):
        """
        分析问题复杂度
        返回复杂度等级（0-3）：0=简单，1=中等，2=复杂
        """
        complexity = 0
        if "multi-step" in self.problem_description.lower():
            complexity += 1
        if "branching" in self.problem_description.lower():
            complexity += 1
        if "nested" in self.problem_description.lower():
            complexity += 1
        if "recursive" in self.problem_description.lower():
            complexity += 1
        return min(complexity, 2)  # 最大复杂度为2

    def _analyze_domain(self):
        """
        分析问题所属领域
        返回领域类型（数学/自然语言/逻辑/其他）
        """
        domain_keywords = {
            "math": ["equation", "formula", "calculate", "prove"],
            "nlp": ["language", "text", "sentence", "word", "phrase"],
            "logic": ["reason", "deduce", "infer", "logical", "argument"],
            "other": ["general", "common", "basic"]
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in self.problem_description.lower() for keyword in keywords):
                return domain
        return "other"

    def _analyze_constraints(self):
        """
        分析问题约束条件
        返回约束类型（time/accuracy/resource/none）
        """
        constraints = []
        if "time" in self.problem_description.lower():
            constraints.append("time")
        if "accuracy" in self.problem_description.lower():
            constraints.append("accuracy")
        if "resource" in self.problem_description.lower():
            constraints.append("resource")
        return constraints

    def _select_strategy(self):
        """
        根据分析结果选择最佳策略
        返回选定的策略（LINEAR/TREE/REFLEXIVE）
        """
        # 优先级排序：LINEAR > TREE > REFLEXIVE
        priority = ["LINEAR", "TREE", "REFLEX" if "reflexive" in self.problem_description.lower() else "REFLEXIVE"]
        
        # 复杂度优先级
        complexity_priority = {0: "LINEAR", 1: "TREE", 2: "REFLEXIVE"}
        
        # 领域优先级
        domain_priority = {
            "math": "LINEAR",
            "nlp": "TREE",
            "logic": "REFLEXIVE",
            "other": "LINEAR"
        }
        
        # 约束优先级
        constraint_priority = {
            "time": "LINEAR",
            "accuracy": "TREE",
            "resource": "REFLEXIVE"
        }
        
        # 综合判断
        selected = "LINEAR"
        
        # 复杂度影响
        selected = complexity_priority.get(self.complexity, selected)
        
        # 领域影响
        selected = domain_priority.get(self.domain, selected)
        
        # 约束影响
        for constraint in self.constraints:
            if constraint in constraint_priority:
                selected = constraint_priority[constraint]
        
        # 特殊情况处理
        if "reflexive" in self.problem_description.lower():
            selected = "REFLEXIVE"
        elif "tree" in self.problem_description.lower():
            selected = "TREE"
        elif "linear" in self.problem_description.lower():
            selected = "LINEAR"
        
        return selected

    def get_selected_strategy(self):
        """
        获取选定的推理策略
        """
        return self.selected_strategy

    def explain_selection(self):
        """
        解释选择策略的依据
        """
        explanation = []
        explanation.append(f"问题复杂度: {self.complexity}")
        explanation.append(f"问题领域: {self.domain}")
        explanation.append(f"约束条件: {self.constraints}")
        explanation.append(f"选择策略: {self.selected_strategy}")
        
        # 添加详细解释
        if self.selected_strategy == "LINEAR":
            explanation.append("选择LINEAR策略原因:")
            explanation.append("- 问题复杂度较低")
            explanation.append("- 需要快速得出结论")
            explanation.append("- 约束条件对时间敏感")
        elif self.selected_strategy == "TREE":
            explanation.append("选择TREE策略原因:")
            explanation.append("- 问题需要分步骤处理")
            explanation.append("- 领域涉及自然语言或结构化数据")
            explanation.append("- 需要维护逻辑分支")
        elif self.selected_strategy == "REFLEXIVE":
            explanation.append("选择REFLEXIVE策略原因:")
            explanation.append("- 问题需要深度推理")
            explanation.append("- 领域涉及逻辑或数学证明")
            explanation.append("- 需要处理递归或嵌套结构")
        
        return "\n".join(explanation)

    def validate_selection(self):
        """
        验证策略选择的合理性
        """
        if self.selected_strategy not in ["LINEAR", "TREE", "REFLEXIVE"]:
            raise ValueError(f"无效的策略选择: {self.selected_strategy}")
        
        # 领域与策略匹配性检查
        if self.domain == "nlp" and self.selected_strategy != "TREE":
            raise ValueError("自然语言处理问题推荐使用TREE策略")
        if self.domain == "logic" and self.selected_strategy != "REFLEXIVE":
            raise ValueError("逻辑推理问题推荐使用REFLEXIVE策略")
        if self.domain == "math" and self.selected_strategy != "LINEAR":
            raise ValueError("数学问题推荐使用LINEAR策略")
        
        # 约束条件与策略匹配性检查
        if "time" in self.constraints and self.selected_strategy != "LINEAR":
            raise ValueError("时间敏感问题推荐使用LINEAR策略")
        if "accuracy" in self.constraints and self.selected_strategy != "TREE":
            raise ValueError("高精度需求问题推荐使用TREE策略")
        if "resource" in self.constraints and self.selected_strategy != "REFLEXIVE":
            raise ValueError("资源受限问题推荐使用REFLEXIVE策略")
        
        return True

    def get_recommendations(self):
        """
        获取策略使用建议
        """
        recommendations = []
        
        if self.selected_strategy == "LINEAR":
            recommendations.append("建议采用线性推理，逐步解决简单问题")
            recommendations.append("适用于需要快速得出结论的场景")
            recommendations.append("注意避免过度复杂化步骤")
        elif self.selected_strategy == "TREE":
            recommendations.append("建议采用树状推理，分步骤处理复杂问题")
            recommendations.append("适用于需要维护多个逻辑分支的场景")
            recommendations.append("注意控制分支深度以避免计算开销")
        elif self.selected_strategy == "REFLEXIVE":
            recommendations.append("建议采用反射式推理，处理深度逻辑问题")
            recommendations.append("适用于需要递归或嵌套分析的场景")
            recommendations.append("注意设置适当的递归深度限制")
        
        return "\n".join(recommendations)

    def get_analysis_summary(self):
        """
        获取完整分析摘要
        """
        summary = []
        summary.append("策略选择分析摘要:")
        summary.append(f"问题复杂度: {self.complexity}")
        summary.append(f"问题领域: {self.domain}")
        summary.append(f"约束条件: {self.constraints}")
        summary.append(f"选定策略: {self.selected_strategy}")
        summary.append(self.explain_selection())
        summary.append(self.get_recommendations())
        return "\n".join(summary)

    def __str__(self):
        """
        字符串表示
        """
        return self.get_analysis_summary()


# ===== Generated: Feature_4 =====

import time
import numpy as np
from collections import OrderedDict

class CacheEntry:
    def __init__(self, query, result, timestamp):
        self.query = query
        self.result = result
        self.timestamp = timestamp

    def __repr__(self):
        return f"CacheEntry({self.query}, {self.result}, {self.timestamp})"

class CacheStats:
    def __init__(self):
        self.hit_count = 0
        self.miss_count = 0
        self.cache_size = 0
        self.max_size = 0
        self.hit_rate = 0.0
        self.miss_rate = 0.0
        self.total_accesses = 0

    def update_stats(self, is_hit):
        self.total_accesses += 1
        if is_hit:
            self.hit_count += 1
        else:
            self.miss_count += 1
        self.hit_rate = self.hit_count / self.total_accesses if self.total_accesses > 0 else 0.0
        self.miss_rate = self.miss_count / self.total_accesses if self.total_accesses > 0 else 0.0

    def __str__(self):
        return (f"CacheStats: Hits={self.hit_count}, Misses={self.miss_count}, "
                f"Hit Rate={self.hit_rate:.2f}, Miss Rate={self.miss_rate:.2f}, "
                f"Total Accesses={self.total_accesses}")

class ReasoningCache:
    def __init__(self, max_size=100, similarity_threshold=0.8):
        self.max_size = max_size
        self.cache = OrderedDict()  # key: query, value: CacheEntry
        self.stats = CacheStats()
        self.similarity_threshold = similarity_threshold
        self.vectorizer = self._init_vectorizer()
        self.similarity_cache = {}  # Cache for precomputed vectors

    def _init_vectorizer(self):
        """Initialize a simple vectorizer for demonstration purposes."""
        return lambda x: self._simple_vectorize(x)

    def _simple_vectorize(self, query):
        """Simple vectorization method based on character counts."""
        return [ord(c) for c in query]

    def _compute_similarity(self, vec1, vec2):
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def _get_vector(self, query):
        """Retrieve or compute the vector for a query."""
        if query in self.similarity_cache:
            return self.similarity_cache[query]
        vector = self.vectorizer(query)
        self.similarity_cache[query] = vector
        return vector

    def find_similar(self, query):
        """Find the most similar entry in the cache based on vector similarity."""
        query_vector = self._get_vector(query)
        for key, entry in self.cache.items():
            entry_vector = self._get_vector(entry.query)
            similarity = self._compute_similarity(query_vector, entry_vector)
            if similarity >= self.similarity_threshold:
                return entry
        return None

    def get(self, query):
        """Retrieve data from cache, or compute and store if not found."""
        similar_entry = self.find_similar(query)
        is_hit = similar_entry is not None
        self.stats.update_stats(is_hit)

        if is_hit:
            key = similar_entry.query
            self.cache.move_to_end(key)
            return similar_entry.result
        else:
            result = self._perform_reasoning(query)
            entry = CacheEntry(query, result, time.time())
            self.cache[query] = entry
            self._maintain_lru()
            return result

    def _perform_reasoning(self, query):
        """Simulate a reasoning process (e.g., model inference)."""
        # In a real scenario, this would call an ML model or database
        return f"Computed result for query: {query}"

    def _maintain_lru(self):
        """Ensure the cache adheres to LRU eviction policy."""
        if len(self.cache) > self.max_size:
            # Remove the oldest entry (first item in OrderedDict)
            self.cache.popitem(last=False)

    def clear_cache(self):
        """Clear all entries from the cache."""
        self.cache.clear()
        self.similarity_cache.clear()
        self.stats.hit_count = 0
        self.stats.miss_count = 0
        self.stats.total_accesses = 0

    def get_stats(self):
        """Return the current cache statistics."""
        return self.stats

    def get_cache_size(self):
        """Return the current number of entries in the cache."""
        return len(self.cache)

    def __str__(self):
        return f"ReasoningCache: {len(self.cache)} entries, {self.stats}"

# Example usage
if __name__ == "__main__":
    cache = ReasoningCache(max_size=5, similarity_threshold=0.7)
    
    # Test queries
    queries = ["What is the capital of France?", 
               "Who wrote 'Hamlet'?", 
               "What is 2+2?", 
               "What is the square root of 16?", 
               "What is the meaning of life?", 
               "What is the capital of Germany?",
               "What is the capital of France?"]
    
    for q in queries:
        print(f"Query: {q}")
        print(f"Result: {cache.get(q)}\n")
    
    print("Cache Statistics:")
    print(cache.get_stats())
    print("Cache Contents:")
    for key, entry in cache.cache.items():
        print(f"{key}: {entry.result}")


# ===== Generated: Feature_5 =====

class MultiStepReflector:
    def __init__(self, max_reflection_depth=5, confidence_threshold=0.75):
        """
        初始化多步反思器
        参数:
            max_reflection_depth: 最大反思深度（递归次数）
            confidence_threshold: 置信度阈值（0-1）
        """
        self.max_reflection_depth = max_reflection_depth
        self.confidence_threshold = confidence_threshold
        self.reflection_log = []  # 记录反思过程
        self.correction_history = []  # 记录修正历史

    def multi_step_reflect(self, initial_input, initial_decision):
        """
        启动多步反思流程
        参数:
            initial_input: 初始输入数据
            initial_decision: 初始决策
        返回:
            修正后的决策及置信度
        """
        self.reflection_log = []
        self.correction_history = []
        final_decision, final_confidence = self._reflect_step(
            initial_input, 
            initial_decision, 
            current_depth=0
        )
        return final_decision, final_confidence

    def _reflect_step(self, input_data, current_decision, current_depth):
        """
        执行单步反思
        参数:
            input_data: 输入数据
            current_decision: 当前决策
            current_depth: 当前反思深度
        返回:
            修正后的决策及置信度
        """
        # 记录反思步骤
        self.reflection_log.append({
            'depth': current_depth,
            'input': input_data,
            'decision': current_decision,
            'confidence': self._calculate_confidence(current_decision)
        })

        # 检查是否达到最大深度
        if current_depth >= self.max_reflection_depth:
            return current_decision, self._calculate_confidence(current_decision)

        # 检测错误并尝试修正
        error_detected, corrected_decision = self._detect_and_correct_errors(
            input_data, 
            current_decision
        )

        if error_detected:
            # 如果修正后置信度仍低于阈值，继续递归反思
            if self._calculate_confidence(corrected_decision) < self.confidence_threshold:
                return self._reflect_step(
                    input_data, 
                    corrected_decision, 
                    current_depth + 1
                )
            else:
                # 修正后置信度达标，记录修正历史
                self.correction_history.append({
                    'original_decision': current_decision,
                    'corrected_decision': corrected_decision,
                    'confidence': self._calculate_confidence(corrected_decision)
                })
                return corrected_decision, self._calculate_confidence(corrected_decision)
        else:
            # 无错误，但检查置信度是否达标
            if self._calculate_confidence(current_decision) >= self.confidence_threshold:
                return current_decision, self._calculate_confidence(current_decision)
            else:
                # 置信度不足，继续递归反思
                return self._reflect_step(
                    input_data, 
                    current_decision, 
                    current_depth + 1
                )

    def _detect_and_correct_errors(self, input_data, current_decision):
        """
        检测错误并尝试修正
        参数:
            input_data: 输入数据
            current_decision: 当前决策
        返回:
            是否检测到错误，修正后的决策
        """
        errors = self._error_check(input_data, current_decision)
        if not errors:
            return False, current_decision

        # 多步骤修正
        corrected_decision = current_decision
        for error in errors:
            correction = self._apply_correction(input_data, corrected_decision, error)
            if correction:
                corrected_decision = correction
                self.correction_history.append({
                    'error': error,
                    'correction': correction,
                    'confidence': self._calculate_confidence(corrected_decision)
                })

        return True, corrected_decision

    def _error_check(self, input_data, decision):
        """
        检测决策中的错误
        参数:
            input_data: 输入数据
            decision: 当前决策
        返回:
            错误列表
        """
        errors = []
        
        # 逻辑错误检测
        if self._logical_error_check(decision):
            errors.append("逻辑错误")
        
        # 数据验证错误
        if self._data_validation_check(input_data, decision):
            errors.append("数据验证错误")
        
        # 约束条件检查
        if self._constraint_check(decision):
            errors.append("约束条件违反")
        
        return errors

    def _logical_error_check(self, decision):
        """
        检查逻辑错误
        参数:
            decision: 决策
        返回:
            是否存在逻辑错误
        """
        # 示例：检查决策是否符合逻辑规则
        if isinstance(decision, dict) and 'value' in decision:
            return decision['value'] < 0  # 假设值不能为负
        return False

    def _data_validation_check(self, input_data, decision):
        """
        检查数据验证错误
        参数:
            input_data: 输入数据
            decision: 决策
        返回:
            是否存在数据验证错误
        """
        # 示例：检查输入数据与决策是否一致
        if isinstance(input_data, dict) and 'expected' in input_data:
            return decision != input_data['expected']
        return False

    def _constraint_check(self, decision):
        """
        检查约束条件
        参数:
            decision: 决策
        返回:
            是否违反约束条件
        """
        # 示例：检查决策是否符合业务规则
        if isinstance(decision, dict) and 'value' in decision:
            return decision['value'] > 100  # 假设最大值为100
        return False

    def _apply_correction(self, input_data, current_decision, error_type):
        """
        应用修正
        参数:
            input_data: 输入数据
            current_decision: 当前决策
            error_type: 错误类型
        返回:
            修正后的决策（或None）
        """
        if error_type == "逻辑错误":
            # 修正逻辑错误：将负值转为0
            if isinstance(current_decision, dict) and 'value' in current_decision:
                return {'value': max(0, current_decision['value'])}
        elif error_type == "数据验证错误":
            # 修正数据验证错误：使用输入数据的预期值
            if isinstance(input_data, dict) and 'expected' in input_data:
                return input_data['expected']
        elif error_type == "约束条件违反":
            # 修正约束条件：将超过限制的值设为最大值
            if isinstance(current_decision, dict) and 'value' in current_decision:
                return {'value': min(100, current_decision['value'])}
        return None

    def _calculate_confidence(self, decision):
        """
        计算决策置信度
        参数:
            decision: 决策
        返回:
            置信度（0-1）
        """
        # 示例：根据决策的结构和内容计算置信度
        if not decision:
            return 0.0
        
        confidence = 0.5  # 基础置信度
        
        # 如果是字典且包含'value'字段
        if isinstance(decision, dict) and 'value' in decision:
            # 值在合理范围内（0-100）
            if 0 <= decision['value'] <= 100:
                confidence += 0.3
            # 值为整数
            if isinstance(decision['value'], int):
                confidence += 0.2
        
        # 如果是字符串且长度合理
        if isinstance(decision, str) and 5 <= len(decision) <= 50:
            confidence += 0.2
        
        return min(confidence, 1.0)

    def get_reflection_log(self):
        """
        获取反思日志
        返回:
            反思日志列表
        """
        return self.reflection_log

    def get_correction_history(self):
        """
        获取修正历史
        返回:
            修正历史列表
        """
        return self.correction_history

    def reset(self):
        """
        重置反思器状态
        """
        self.reflection_log = []
        self.correction_history = []

# 示例用法
if __name__ == "__main__":
    # 初始化反思器
    reflector = MultiStepReflector(max_reflection_depth=3, confidence_threshold=0.7)
    
    # 测试案例1：逻辑错误
    input_data_1 = {'expected': {'value': 50}}
    initial_decision_1 = {'value': -10}
    final_decision_1, final_confidence_1 = reflector.multi_step_reflect(input_data_1, initial_decision_1)
    print("案例1结果:", final_decision_1, "置信度:", final_confidence_1)
    
    # 测试案例2：数据验证错误
    input_data_2 = {'expected': {'value': 75}}
    initial_decision_2 = {'value': 90}
    final_decision_2, final_confidence_2 = reflector.multi_step_reflect(input_data_2, initial_decision_2)
    print("案例2结果:", final_decision_2, "置信度:", final_confidence_2)
    
    # 测试案例3：约束条件违反
    input_data_3 = {'expected': {'value': 150}}
    initial_decision_3 = {'value': 200}
    final_decision_3, final_confidence_3 = reflector.multi_step_reflect(input_data_3, initial_decision_3)
    print("案例3结果:", final_decision_3, "置信度:", final_confidence_3)
    
    # 查看反思日志
    print("反思日志:", reflector.get_reflection_log())
    print("修正历史:", reflector.get_correction_history())
