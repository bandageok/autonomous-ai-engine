"""Monitoring - 监控指标"""
from typing import Dict, List, Callable
from datetime import datetime
from collections import defaultdict, deque
import time

class MetricsCollector:
    """指标收集器"""
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = {}
        self.histograms = defaultdict(lambda: deque(maxlen=1000))
        
    def increment(self, name: str, value: int = 1):
        """增加计数器"""
        self.counters[name] += value
        
    def gauge(self, name: str, value: float):
        """设置仪表值"""
        self.gauges[name] = value
        
    def histogram(self, name: str, value: float):
        """记录直方图值"""
        self.histograms[name].append(value)
        
    def timing(self, name: str, duration_ms: float):
        """记录时间"""
        self.histograms[f"{name}.duration"].append(duration_ms)
        
    def get_counter(self, name: str) -> int:
        return self.counters.get(name, 0)
        
    def get_gauge(self, name: str):
        return self.gauges.get(name)
        
    def get_histogram_stats(self, name: str) -> Dict:
        """获取直方图统计"""
        values = list(self.histograms.get(name, []))
        if not values:
            return {}
        sorted_values = sorted(values)
        n = len(sorted_values)
        return {
            "count": n,
            "sum": sum(values),
            "mean": sum(values) / n,
            "min": sorted_values[0],
            "max": sorted_values[-1],
            "p50": sorted_values[n // 2],
            "p95": sorted_values[int(n * 0.95)]
        }
        
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {k: len(v) for k, v in self.histograms.items()}
        }

class HealthChecker:
    """健康检查"""
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        
    def register(self, name: str, check_func: Callable):
        """注册检查"""
        self.checks[name] = check_func
        
    async def check(self, name: str) -> bool:
        """执行检查"""
        if name not in self.checks:
            return False
        try:
            func = self.checks[name]
            if asyncio.iscoroutinefunction(func):
                return await func()
            return func()
        except:
            return False
            
    async def check_all(self) -> Dict[str, bool]:
        """执行所有检查"""
        results = {}
        for name in self.checks:
            results[name] = await self.check(name)
        return results

import asyncio
