"""Main Evaluator - AI输出评估器"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import hashlib

logger = logging.getLogger(__name__)


class EvaluationStatus(Enum):
    """评估状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ThresholdMode(Enum):
    """阈值模式"""
    STRICT = "strict"
    BALANCED = "balanced"
    LENIENT = "lenient"


@dataclass
class EvaluationContext:
    """评估上下文"""
    task_id: str
    prompt: str
    expected_output: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EvaluationResult:
    """评估结果"""
    context: EvaluationContext
    status: EvaluationStatus
    scores: Dict[str, float] = field(default_factory=dict)
    overall_score: float = 0.0
    passed: bool = False
    details: Dict = field(default_factory=dict)
    error: Optional[str] = None
    evaluation_time: float = 0.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.context.task_id,
            "status": self.status.value,
            "scores": self.scores,
            "overall_score": self.overall_score,
            "passed": self.passed,
            "details": self.details,
            "error": self.error,
            "evaluation_time": self.evaluation_time,
            "timestamp": self.context.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """转换为JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class MetricAdapter:
    """指标适配器"""
    def __init__(self, metric: Any, weight: float = 1.0, threshold: float = 0.5):
        self.metric = metric
        self.weight = weight
        self.threshold = threshold
    
    async def evaluate(self, prompt: str, output: str, context: Dict) -> float:
        """执行评估"""
        if asyncio.iscoroutinefunction(self.metric.compute):
            return await self.metric.compute(prompt, output, context)
        return self.metric.compute(prompt, output, context)


class AIEvaluator:
    """AI输出评估器"""
    
    def __init__(
        self,
        threshold_mode: ThresholdMode = ThresholdMode.BALANCED,
        min_pass_score: float = 0.6,
        enable_caching: bool = True,
        cache_ttl: int = 3600
    ):
        self.threshold_mode = threshold_mode
        self.min_pass_score = min_pass_score
        self.enable_caching = enable_caching
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, EvaluationResult] = {}
        self._metrics: Dict[str, MetricAdapter] = {}
        self._hooks: List[Callable] = []
        self._thresholds = self._load_thresholds()
        
    def _load_thresholds(self) -> Dict[str, float]:
        """加载阈值配置"""
        presets = {
            ThresholdMode.STRICT: 0.8,
            ThresholdMode.BALANCED: 0.6,
            ThresholdMode.LENIENT: 0.4
        }
        default_threshold = presets.get(self.threshold_mode, 0.6)
        
        return {
            "relevance": default_threshold,
            "coherence": default_threshold,
            "toxicity": 1.0 - default_threshold,
            "fluency": default_threshold,
            "accuracy": default_threshold,
            "safety": default_threshold
        }
    
    def register_metric(
        self, 
        name: str, 
        metric: Any, 
        weight: float = 1.0,
        threshold: Optional[float] = None
    ):
        """注册指标"""
        effective_threshold = threshold or self._thresholds.get(name, 0.5)
        self._metrics[name] = MetricAdapter(metric, weight, effective_threshold)
        logger.info(f"Registered metric: {name} (weight={weight}, threshold={effective_threshold})")
    
    def unregister_metric(self, name: str):
        """注销指标"""
        if name in self._metrics:
            del self._metrics[name]
            logger.info(f"Unregistered metric: {name}")
    
    def add_hook(self, hook: Callable[[EvaluationResult], Any]):
        """添加钩子"""
        self._hooks.append(hook)
    
    def remove_hook(self, hook: Callable):
        """移除钩子"""
        if hook in self._hooks:
            self._hooks.remove(hook)
    
    def _get_cache_key(self, prompt: str, output: str) -> str:
        """获取缓存键"""
        content = f"{prompt}:{output}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[EvaluationResult]:
        """获取缓存结果"""
        if not self.enable_caching:
            return None
            
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.now() - cached.context.timestamp).total_seconds()
            if age < self.cache_ttl:
                logger.debug(f"Cache hit for key: {cache_key[:16]}...")
                return cached
            else:
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: EvaluationResult):
        """缓存结果"""
        if self.enable_caching:
            self._cache[cache_key] = result
    
    async def evaluate(
        self,
        prompt: str,
        output: str,
        expected_output: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        run_hooks: bool = True
    ) -> EvaluationResult:
        """执行评估"""
        start_time = datetime.now()
        task_id = task_id or f"eval_{start_time.timestamp()}"
        
        context = EvaluationContext(
            task_id=task_id,
            prompt=prompt,
            expected_output=expected_output,
            metadata=metadata or {}
        )
        
        cache_key = self._get_cache_key(prompt, output)
        cached = self._get_cached_result(cache_key)
        if cached:
            cached.context.timestamp = datetime.now()
            return cached
        
        result = EvaluationResult(
            context=context,
            status=EvaluationStatus.RUNNING
        )
        
        try:
            if not self._metrics:
                raise ValueError("No metrics registered")
            
            scores = {}
            details = {}
            
            for name, adapter in self._metrics.items():
                try:
                    score = await adapter.evaluate(prompt, output, context.metadata)
                    scores[name] = score
                    
                    details[name] = {
                        "score": score,
                        "weight": adapter.weight,
                        "threshold": adapter.threshold,
                        "passed": score >= adapter.threshold
                    }
                except Exception as e:
                    logger.error(f"Metric {name} failed: {e}")
                    scores[name] = 0.0
                    details[name] = {"error": str(e)}
            
            result.scores = scores
            result.details = details
            
            weighted_sum = 0.0
            total_weight = 0.0
            for name, score in scores.items():
                adapter = self._metrics[name]
                weighted_sum += score * adapter.weight
                total_weight += adapter.weight
            
            result.overall_score = weighted_sum / total_weight if total_weight > 0 else 0.0
            result.passed = result.overall_score >= self.min_pass_score
            result.status = EvaluationStatus.COMPLETED
            
            if run_hooks:
                await self._run_hooks(result)
                
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            result.status = EvaluationStatus.FAILED
            result.error = str(e)
        
        result.evaluation_time = (datetime.now() - start_time).total_seconds()
        
        self._cache_result(cache_key, result)
        
        return result
    
    async def evaluate_batch(
        self,
        items: List[Dict[str, Any]],
        run_hooks: bool = True
    ) -> List[EvaluationResult]:
        """批量评估"""
        tasks = [
            self.evaluate(
                prompt=item["prompt"],
                output=item["output"],
                expected_output=item.get("expected"),
                task_id=item.get("task_id"),
                metadata=item.get("metadata"),
                run_hooks=run_hooks
            )
            for item in items
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _run_hooks(self, result: EvaluationResult):
        """运行钩子"""
        for hook in self._hooks:
            try:
                if asyncio.iscoroutinefunction(hook):
                    await hook(result)
                else:
                    hook(result)
            except Exception as e:
                logger.error(f"Hook error: {e}")
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("Evaluation cache cleared")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self._cache:
            return {"total_evaluations": 0}
        
        completed = [r for r in self._cache.values() if r.status == EvaluationStatus.COMPLETED]
        passed = [r for r in completed if r.passed]
        
        scores = [r.overall_score for r in completed]
        
        return {
            "total_evaluations": len(self._cache),
            "completed": len(completed),
            "passed": len(passed),
            "pass_rate": len(passed) / len(completed) if completed else 0.0,
            "avg_score": sum(scores) / len(scores) if scores else 0.0,
            "registered_metrics": list(self._metrics.keys())
        }
