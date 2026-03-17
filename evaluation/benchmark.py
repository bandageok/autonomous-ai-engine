"""Benchmark Framework - 基准测试框架"""
import asyncio
import logging
import time
import json
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import statistics
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class BenchmarkStatus(Enum):
    """基准测试状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TestCase:
    """测试用例"""
    id: str
    prompt: str
    expected_output: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    timeout: float = 30.0


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    benchmark_id: str
    status: BenchmarkStatus
    total_cases: int = 0
    passed_cases: int = 0
    failed_cases: int = 0
    pass_rate: float = 0.0
    avg_score: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    std_deviation: float = 0.0
    avg_evaluation_time: float = 0.0
    results: List[Dict] = field(default_factory=list)
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "benchmark_id": self.benchmark_id,
            "status": self.status.value,
            "total_cases": self.total_cases,
            "passed_cases": self.passed_cases,
            "failed_cases": self.failed_cases,
            "pass_rate": self.pass_rate,
            "avg_score": self.avg_score,
            "min_score": self.min_score,
            "max_score": self.max_score,
            "std_deviation": self.std_deviation,
            "avg_evaluation_time": self.avg_evaluation_time,
            "results": self.results,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "metadata": self.metadata
        }


@dataclass
class BenchmarkConfig:
    """基准测试配置"""
    name: str
    description: str = ""
    parallel: bool = False
    max_workers: int = 4
    timeout: float = 60.0
    fail_fast: bool = False
    save_results: bool = True
    output_path: str = "./benchmark_results"


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total: int):
        self.total = total
        self.completed = 0
        self.failed = 0
        self.start_time = time.time()
    
    def update(self, success: bool = True):
        """更新进度"""
        self.completed += 1
        if not success:
            self.failed += 1
    
    def get_progress(self) -> Dict:
        """获取进度"""
        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0
        eta = (self.total - self.completed) / rate if rate > 0 else 0
        
        return {
            "completed": self.completed,
            "total": self.total,
            "failed": self.failed,
            "elapsed": elapsed,
            "eta": eta,
            "progress_pct": (self.completed / self.total * 100) if self.total > 0 else 0
        }


class BenchmarkRunner:
    """基准测试运行器"""
    
    def __init__(
        self,
        evaluator: Any,
        config: Optional[BenchmarkConfig] = None
    ):
        self.evaluator = evaluator
        self.config = config or BenchmarkConfig(name="default")
        self._test_cases: List[TestCase] = []
        self._callbacks: List[Callable] = []
    
    def add_test_case(self, test_case: TestCase):
        """添加测试用例"""
        self._test_cases.append(test_case)
        logger.debug(f"Added test case: {test_case.id}")
    
    def add_test_cases(self, test_cases: List[TestCase]):
        """批量添加测试用例"""
        self._test_cases.extend(test_cases)
        logger.info(f"Added {len(test_cases)} test cases")
    
    def load_test_cases_from_json(self, path: str):
        """从JSON文件加载测试用例"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data.get("test_cases", []):
                test_case = TestCase(
                    id=item["id"],
                    prompt=item["prompt"],
                    expected_output=item.get("expected"),
                    metadata=item.get("metadata", {}),
                    timeout=item.get("timeout", 30.0)
                )
                self.add_test_case(test_case)
            
            logger.info(f"Loaded {len(self._test_cases)} test cases from {path}")
        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
            raise
    
    def register_callback(self, callback: Callable):
        """注册回调函数"""
        self._callbacks.append(callback)
    
    def _run_callbacks(self, result: BenchmarkResult):
        """执行回调"""
        for callback in self._callbacks:
            try:
                callback(result)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def _run_single_test(
        self,
        test_case: TestCase,
        progress: ProgressTracker
    ) -> Dict:
        """运行单个测试"""
        try:
            result = await asyncio.wait_for(
                self.evaluator.evaluate(
                    prompt=test_case.prompt,
                    output="",  # Placeholder - actual output would come from the AI system
                    expected_output=test_case.expected_output,
                    task_id=test_case.id,
                    metadata=test_case.metadata
                ),
                timeout=test_case.timeout
            )
            
            test_result = {
                "test_id": test_case.id,
                "passed": result.passed,
                "score": result.overall_score,
                "evaluation_time": result.evaluation_time,
                "status": result.status.value,
                "error": result.error
            }
            
            progress.update(result.passed)
            return test_result
            
        except asyncio.TimeoutError:
            progress.update(False)
            return {
                "test_id": test_case.id,
                "passed": False,
                "score": 0.0,
                "status": "timeout",
                "error": f"Test timed out after {test_case.timeout}s"
            }
        except Exception as e:
            logger.error(f"Test {test_case.id} failed: {e}")
            progress.update(False)
            return {
                "test_id": test_case.id,
                "passed": False,
                "score": 0.0,
                "status": "error",
                "error": str(e)
            }
    
    async def run(self) -> BenchmarkResult:
        """运行基准测试"""
        benchmark_id = f"{self.config.name}_{int(time.time())}"
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            status=BenchmarkStatus.RUNNING,
            start_time=datetime.now()
        )
        
        if not self._test_cases:
            result.status = BenchmarkStatus.FAILED
            result.error = "No test cases defined"
            return result
        
        result.total_cases = len(self._test_cases)
        progress = ProgressTracker(result.total_cases)
        
        logger.info(f"Starting benchmark: {self.config.name} with {result.total_cases} test cases")
        
        try:
            if self.config.parallel:
                results = await self._run_parallel(progress)
            else:
                results = await self._run_sequential(progress)
            
            result.results = results
            result.end_time = datetime.now()
            
            passed = [r for r in results if r.get("passed", False)]
            result.passed_cases = len(passed)
            result.failed_cases = result.total_cases - result.passed_cases
            result.pass_rate = result.passed_cases / result.total_cases if result.total_cases > 0 else 0
            
            scores = [r.get("score", 0.0) for r in results]
            if scores:
                result.avg_score = statistics.mean(scores)
                result.min_score = min(scores)
                result.max_score = max(scores)
                result.std_deviation = statistics.stdev(scores) if len(scores) > 1 else 0.0
            
            evaluation_times = [r.get("evaluation_time", 0.0) for r in results]
            if evaluation_times:
                result.avg_evaluation_time = statistics.mean(evaluation_times)
            
            result.status = BenchmarkStatus.COMPLETED
            logger.info(f"Benchmark completed: {result.pass_rate*100:.1f}% pass rate")
            
        except Exception as e:
            logger.error(f"Benchmark failed: {e}")
            result.status = BenchmarkStatus.FAILED
            result.error = str(e)
            result.end_time = datetime.now()
        
        if self.config.save_results:
            self._save_results(result)
        
        self._run_callbacks(result)
        
        return result
    
    async def _run_sequential(self, progress: ProgressTracker) -> List[Dict]:
        """顺序运行测试"""
        results = []
        
        for test_case in self._test_cases:
            result = await self._run_single_test(test_case, progress)
            results.append(result)
            
            if self.config.fail_fast and not result["passed"]:
                logger.warning("Fail-fast triggered, stopping benchmark")
                break
        
        return results
    
    async def _run_parallel(self, progress: ProgressTracker) -> List[Dict]:
        """并行运行测试"""
        semaphore = asyncio.Semaphore(self.config.max_workers)
        
        async def limited_run(test_case: TestCase):
            async with semaphore:
                return await self._run_single_test(test_case, progress)
        
        tasks = [limited_run(tc) for tc in self._test_cases]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for r in results:
            if isinstance(r, Exception):
                processed_results.append({
                    "passed": False,
                    "score": 0.0,
                    "status": "error",
                    "error": str(r)
                })
            else:
                processed_results.append(r)
        
        return processed_results
    
    def _save_results(self, result: BenchmarkResult):
        """保存结果"""
        import os
        os.makedirs(self.config.output_path, exist_ok=True)
        
        filename = f"{result.benchmark_id}.json"
        filepath = os.path.join(self.config.output_path, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)
        
        logger.info(f"Results saved to {filepath}")
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "total_test_cases": len(self._test_cases),
            "config": {
                "name": self.config.name,
                "parallel": self.config.parallel,
                "max_workers": self.config.max_workers,
                "timeout": self.config.timeout
            }
        }


class BenchmarkSuite:
    """基准测试套件"""
    
    def __init__(self):
        self._benchmarks: Dict[str, BenchmarkRunner] = {}
        self._results: Dict[str, BenchmarkResult] = {}
    
    def register_benchmark(self, name: str, runner: BenchmarkRunner):
        """注册基准测试"""
        self._benchmarks[name] = runner
        logger.info(f"Registered benchmark: {name}")
    
    async def run_benchmark(self, name: str) -> BenchmarkResult:
        """运行指定基准测试"""
        if name not in self._benchmarks:
            raise ValueError(f"Benchmark not found: {name}")
        
        runner = self._benchmarks[name]
        result = await runner.run()
        self._results[name] = result
        
        return result
    
    async def run_all(self) -> Dict[str, BenchmarkResult]:
        """运行所有基准测试"""
        results = {}
        
        for name, runner in self._benchmarks.items():
            logger.info(f"Running benchmark: {name}")
            result = await runner.run()
            results[name] = result
            self._results[name] = result
        
        return results
    
    def get_result(self, name: str) -> Optional[BenchmarkResult]:
        """获取基准测试结果"""
        return self._results.get(name)
    
    def get_summary(self) -> Dict:
        """获取汇总信息"""
        if not self._results:
            return {"total_benchmarks": 0}
        
        total_cases = sum(r.total_cases for r in self._results.values())
        total_passed = sum(r.passed_cases for r in self._results.values())
        
        return {
            "total_benchmarks": len(self._results),
            "total_test_cases": total_cases,
            "total_passed": total_passed,
            "overall_pass_rate": total_passed / total_cases if total_cases > 0 else 0,
            "benchmarks": {
                name: {
                    "pass_rate": r.pass_rate,
                    "avg_score": r.avg_score,
                    "status": r.status.value
                }
                for name, r in self._results.items()
            }
        }
