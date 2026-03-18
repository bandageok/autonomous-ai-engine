"""Monitoring - 监控指标 + 高级监控系统"""
import asyncio
import logging
import time
import json
from typing import Dict, List, Callable, Any, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import threading
import statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnomalyType(Enum):
    """异常类型"""
    SPIKE = "spike"
    DROP = "drop"
    TREND = "trend"
    FLAT = "flat"

class AlertSeverity(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AlertStatus(Enum):
    """告警状态"""
    FIRED = "fired"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"

@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric_name: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown_seconds: int = 60
    description: str = ""

@dataclass
class Alert:
    """告警实例"""
    id: str
    rule_name: str
    metric_name: str
    value: float
    threshold: float
    severity: AlertSeverity
    status: AlertStatus
    fired_at: datetime
    resolved_at: Optional[datetime] = None
    message: str = ""

@dataclass
class MetricDataPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)

class AnomalyDetector:
    """异常检测器"""
    def __init__(self, window_size: int = 100, sensitivity: float = 2.0):
        self.window_size = window_size
        self.sensitivity = sensitivity
        self.metric_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=window_size))
    
    def add_data_point(self, metric_name: str, value: float):
        """添加数据点"""
        self.metric_history[metric_name].append(value)
    
    def detect_anomalies(self, metric_name: str, value: float) -> Optional[AnomalyType]:
        """检测异常"""
        history = list(self.metric_history.get(metric_name, []))
        
        if len(history) < 10:
            return None
        
        mean = statistics.mean(history)
        std = statistics.stdev(history)
        
        if std == 0:
            return None
        
        z_score = (value - mean) / std
        
        if z_score > self.sensitivity:
            return AnomalyType.SPIKE
        elif z_score < -self.sensitivity:
            return AnomalyType.DROP
        
        return None
    
    def get_statistics(self, metric_name: str) -> Dict:
        """获取统计信息"""
        history = list(self.metric_history.get(metric_name, []))
        
        if not history:
            return {}
        
        sorted_values = sorted(history)
        n = len(sorted_values)
        
        return {
            'count': n,
            'mean': statistics.mean(history),
            'median': statistics.median(history),
            'std': statistics.stdev(history) if n > 1 else 0,
            'min': min(history),
            'max': max(history),
            'p50': sorted_values[n // 2],
            'p95': sorted_values[int(n * 0.95)],
            'p99': sorted_values[int(n * 0.99)]
        }

class TrendPredictor:
    """趋势预测器"""
    def __init__(self, lookback_points: int = 50):
        self.lookback_points = lookback_points
        self.metric_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=lookback_points * 2))
    
    def add_data_point(self, metric_name: str, value: float):
        """添加数据点"""
        self.metric_data[metric_name].append(value)
    
    def predict_next(self, metric_name: str) -> Optional[float]:
        """预测下一个值"""
        data = list(self.metric_data.get(metric_name, []))
        
        if len(data) < self.lookback_points:
            return None
        
        # 简单的线性回归预测
        recent = data[-self.lookback_points:]
        n = len(recent)
        
        x = list(range(n))
        y = recent
        
        x_mean = sum(x) / n
        y_mean = sum(y) / n
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return y_mean
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # 预测下一个点
        predicted = slope * n + intercept
        
        return predicted
    
    def detect_trend(self, metric_name: str) -> str:
        """检测趋势"""
        data = list(self.metric_data.get(metric_name, []))
        
        if len(data) < 10:
            return "unknown"
        
        recent = data[-10:]
        
        if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
            return "increasing"
        elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
            return "decreasing"
        else:
            return "stable"

class AlertEngine:
    """告警引擎"""
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.last_triggered: Dict[str, datetime] = {}
        self.alert_handlers: List[Callable] = []
    
    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules[rule.name] = rule
        logger.info(f"Alert rule added: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """删除告警规则"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Alert rule removed: {rule_name}")
    
    def register_handler(self, handler: Callable):
        """注册告警处理器"""
        self.alert_handlers.append(handler)
    
    def evaluate_rule(self, rule: AlertRule, metric_value: float) -> bool:
        """评估规则"""
        if not rule.enabled:
            return False
        
        # 冷却检查
        if rule.name in self.last_triggered:
            time_since_last = (datetime.now() - self.last_triggered[rule.name]).total_seconds()
            if time_since_last < rule.cooldown_seconds:
                return False
        
        # 条件评估
        if rule.condition == "gt":
            return metric_value > rule.threshold
        elif rule.condition == "lt":
            return metric_value < rule.threshold
        elif rule.condition == "eq":
            return abs(metric_value - rule.threshold) < 0.0001
        elif rule.condition == "gte":
            return metric_value >= rule.threshold
        elif rule.condition == "lte":
            return metric_value <= rule.threshold
        
        return False
    
    async def check_metric(self, metric_name: str, value: float):
        """检查指标"""
        for rule_name, rule in self.rules.items():
            if rule.metric_name == metric_name:
                if self.evaluate_rule(rule, value):
                    await self._fire_alert(rule, value)
                elif rule_name in self.active_alerts:
                    await self._resolve_alert(rule_name)
    
    async def _fire_alert(self, rule: AlertRule, value: float):
        """触发告警"""
        alert_id = f"{rule.name}_{datetime.now().timestamp()}"
        
        alert = Alert(
            id=alert_id,
            rule_name=rule.name,
            metric_name=rule.metric_name,
            value=value,
            threshold=rule.threshold,
            severity=rule.severity,
            status=AlertStatus.FIRED,
            fired_at=datetime.now(),
            message=f"{rule.description}: {value} {rule.condition} {rule.threshold}"
        )
        
        self.active_alerts[rule.name] = alert
        self.last_triggered[rule.name] = datetime.now()
        
        logger.warning(f"Alert fired: {alert.message}")
        
        # 调用告警处理器
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
    
    async def _resolve_alert(self, rule_name: str):
        """解除告警"""
        if rule_name in self.active_alerts:
            alert = self.active_alerts[rule_name]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            self.alert_history.append(alert)
            del self.active_alerts[rule_name]
            
            logger.info(f"Alert resolved: {rule_name}")
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return list(self.active_alerts.values())

class MetricsAggregator:
    """多维指标聚合器"""
    def __init__(self):
        self.aggregations: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(list))
    
    def record(self, metric_name: str, value: float, dimensions: Dict[str, str] = None):
        """记录指标"""
        if dimensions:
            # 多维聚合
            key = ":".join(f"{k}={v}" for k, v in sorted(dimensions.items()))
            self.aggregations[metric_name][key].append(value)
        else:
            self.aggregations[metric_name]["_global"].append(value)
    
    def get_aggregated_stats(self, metric_name: str) -> Dict:
        """获取聚合统计"""
        if metric_name not in self.aggregations:
            return {}
        
        result = {}
        for dim_key, values in self.aggregations[metric_name].items():
            if values:
                result[dim_key] = {
                    'count': len(values),
                    'sum': sum(values),
                    'mean': statistics.mean(values),
                    'min': min(values),
                    'max': max(values)
                }
        
        return result

class MetricsExporter:
    """指标导出器"""
    def __init__(self):
        self.export_handlers: Dict[str, Callable] = {}
    
    def register_exporter(self, name: str, handler: Callable):
        """注册导出器"""
        self.export_handlers[name] = handler
    
    async def export_to_prometheus(self, metrics_collector) -> str:
        """导出为Prometheus格式"""
        lines = []
        
        # 导出counters
        for name, value in metrics_collector.counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")
        
        # 导出gauges
        for name, value in metrics_collector.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        
        return "\n".join(lines)
    
    async def export_to_json(self, metrics_collector) -> str:
        """导出为JSON格式"""
        return json.dumps(metrics_collector.get_stats(), indent=2)

class MetricsArchiver:
    """指标数据归档器"""
    def __init__(self, retention_days: int = 30, compression: bool = True):
        self.retention_days = retention_days
        self.compression = compression
        self.archive: Dict[str, List[MetricDataPoint]] = defaultdict(list)
        self.archive_lock = threading.Lock()
    
    def archive_metric(self, metric_name: str, value: float, tags: Dict[str, str] = None):
        """归档指标"""
        with self.archive_lock:
            data_point = MetricDataPoint(
                timestamp=datetime.now(),
                value=value,
                tags=tags or {}
            )
            self.archive[metric_name].append(data_point)
    
    def get_archived_metrics(
        self,
        metric_name: str,
        start_time: datetime = None,
        end_time: datetime = None
    ) -> List[MetricDataPoint]:
        """获取归档指标"""
        with self.archive_lock:
            data_points = self.archive.get(metric_name, [])
            
            if start_time:
                data_points = [dp for dp in data_points if dp.timestamp >= start_time]
            if end_time:
                data_points = [dp for dp in data_points if dp.timestamp <= end_time]
            
            return data_points
    
    def cleanup_old_data(self):
        """清理旧数据"""
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        
        with self.archive_lock:
            for metric_name in list(self.archive.keys()):
                self.archive[metric_name] = [
                    dp for dp in self.archive[metric_name]
                    if dp.timestamp >= cutoff
                ]
        
        logger.info(f"Cleaned up metrics older than {self.retention_days} days")

class MetricsCollector:
    """指标收集器"""
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = {}
        self.histograms = defaultdict(lambda: deque(maxlen=1000))
        self.anomaly_detector = AnomalyDetector()
        self.trend_predictor = TrendPredictor()
        self.alert_engine = AlertEngine()
        self.aggregator = MetricsAggregator()
        self.exporter = MetricsExporter()
        self.archiver = MetricsArchiver()
        
        # 注册默认导出器
        self.exporter.register_exporter("prometheus", self.exporter.export_to_prometheus)
        self.exporter.register_exporter("json", self.exporter.export_to_json)
        
        self._lock = threading.Lock()
    
    def increment(self, name: str, value: int = 1):
        """增加计数器"""
        with self._lock:
            self.counters[name] += value
            self._check_and_record(name, float(self.counters[name]))
    
    def gauge(self, name: str, value: float):
        """设置仪表值"""
        with self._lock:
            self.gauges[name] = value
            self._check_and_record(name, value)
    
    def histogram(self, name: str, value: float):
        """记录直方图值"""
        with self._lock:
            self.histograms[name].append(value)
            self.anomaly_detector.add_data_point(name, value)
            self.trend_predictor.add_data_point(name, value)
            self._check_and_record(name, value)
    
    def timing(self, name: str, duration_ms: float):
        """记录时间"""
        self.histogram(f"{name}.duration", duration_ms)
    
    def _check_and_record(self, name: str, value: float):
        """检查并记录"""
        # 触发告警引擎
        asyncio.create_task(self.alert_engine.check_metric(name, value))
        
        # 归档
        self.archiver.archive_metric(name, value)
    
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
    
    def get_anomaly_detection(self, metric_name: str) -> Dict:
        """获取异常检测结果"""
        return self.anomaly_detector.get_statistics(metric_name)
    
    def detect_anomaly(self, metric_name: str, value: float) -> Optional[AnomalyType]:
        """检测异常"""
        return self.anomaly_detector.detect_anomalies(metric_name, value)
    
    def predict_next(self, metric_name: str) -> Optional[float]:
        """预测下一值"""
        return self.trend_predictor.predict_next(metric_name)
    
    def get_trend(self, metric_name: str) -> str:
        """获取趋势"""
        return self.trend_predictor.detect_trend(metric_name)
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_engine.add_rule(rule)
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return self.alert_engine.get_active_alerts()
    
    def get_aggregated_stats(self, metric_name: str) -> Dict:
        """获取聚合统计"""
        return self.aggregator.get_aggregated_stats(metric_name)
    
    async def export(self, format: str = "prometheus") -> str:
        """导出指标"""
        exporter = self.exporter.export_handlers.get(format)
        if exporter:
            if asyncio.iscoroutinefunction(exporter):
                return await exporter(self)
            return exporter(self)
        return ""
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {k: len(v) for k, v in self.histograms.items()},
            "active_alerts": len(self.alert_engine.get_active_alerts())
        }

class HealthChecker:
    """健康检查"""
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.check_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self._lock = threading.Lock()
    
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
                result = await func()
            else:
                result = func()
            
            with self._lock:
                self.check_history[name].append({
                    'timestamp': datetime.now(),
                    'healthy': result
                })
            
            return result
        except:
            return False
    
    async def check_all(self) -> Dict[str, bool]:
        """执行所有检查"""
        results = {}
        for name in self.checks:
            results[name] = await self.check(name)
        return results
    
    def get_health_history(self, name: str) -> List[Dict]:
        """获取健康检查历史"""
        return list(self.check_history.get(name, []))
    
    def get_overall_health(self) -> Dict:
        """获取总体健康状态"""
        results = asyncio.run(self.check_all())
        
        healthy_count = sum(1 for v in results.values() if v)
        total_count = len(results)
        
        return {
            'status': 'healthy' if healthy_count == total_count else 'degraded',
            'healthy_checks': healthy_count,
            'total_checks': total_count,
            'checks': results
        }
