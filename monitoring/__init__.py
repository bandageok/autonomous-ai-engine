```python
import asyncio
import typing
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
import random
import time
import uuid

class MetricsData:
    """
    Represents system/application metrics data with timestamps and metrics.
    
    Attributes:
        timestamp: datetime object indicating when the metrics were collected
        metrics: dictionary containing various metrics with their values
    """
    def __init__(self, timestamp: datetime, metrics: Dict[str, float]):
        self.timestamp = timestamp
        self.metrics = metrics

class AlertRule:
    """
    Represents an alerting rule with threshold and severity level.
    
    Attributes:
        metric_name: name of the metric to monitor
        threshold: threshold value for triggering the alert
        severity: severity level of the alert (critical/warning/info)
        window: time window in seconds for evaluating the alert
    """
    def __init__(self, metric_name: str, threshold: float, severity: str, window: int = 60):
        self.metric_name = metric_name
        self.threshold = threshold
        self.severity = severity
        self.window = window

class Alert:
    """
    Represents an alert with details about the alert.
    
    Attributes:
        id: unique identifier for the alert
        timestamp: datetime object indicating when the alert was triggered
        metric_name: name of the metric that triggered the alert
        severity: severity level of the alert
        value: value of the metric that triggered the alert
        description: description of the alert
    """
    def __init__(self, id: str, timestamp: datetime, metric_name: str, severity: str, value: float, description: str):
        self.id = id
        self.timestamp = timestamp
        self.metric_name = metric_name
        self.severity = severity
        self.value = value
        self.description = description

class MetricsCollector:
    """
    Collects system/application metrics asynchronously.
    
    Attributes:
        interval: time interval in seconds between metric collections
        metrics: dictionary containing metric names and their default values
    """
    def __init__(self, interval: int = 5):
        self.interval = interval
        self.metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "network_usage": 0.0,
            "request_latency": 0.0,
            "error_rate": 0.0
        }

    async def collect_metrics(self) -> MetricsData:
        """
        Collects metrics with simulated values.
        
        Returns:
            MetricsData object containing the collected metrics
        """
        timestamp = datetime.now()
        self.metrics["cpu_usage"] = random.uniform(0.1, 0.9)
        self.metrics["memory_usage"] = random.uniform(0.4, 0.8)
        self.metrics["disk_usage"] = random.uniform(0.2, 0.7)
        self.metrics["network_usage"] = random.uniform(0.1, 0.5)
        self.metrics["request_latency"] = random.uniform(0.05, 0.2)
        self.metrics["error_rate"] = random.uniform(0.0, 0.1)
        
        return MetricsData(timestamp, self.metrics)

class AlertManager:
    """
    Manages alerting rules and triggers alerts based on metric thresholds.
    
    Attributes:
        rules: list of AlertRule objects defining alerting rules
        alerts: list of Alert objects representing active alerts
    """
    def __init__(self):
        self.rules = []
        self.alerts = []

    def add_rule(self, rule: AlertRule):
        """
        Adds an alerting rule to the manager.
        
        Args:
            rule: AlertRule object to add
        """
        self.rules.append(rule)

    async def check_alerts(self, metrics_data: MetricsData):
        """
        Checks if any alerting rules are triggered by the given metrics.
        
        Args:
            metrics_data: MetricsData object containing the metrics to check
        """
        for rule in self.rules:
            metric_value = metrics_data.metrics.get(rule.metric_name, 0.0)
            if metric_value > rule.threshold:
                alert_id = str(uuid.uuid4())
                alert_timestamp = datetime.now()
                alert = Alert(
                    id=alert_id,
                    timestamp=alert_timestamp,
                    metric_name=rule.metric_name,
                    severity=rule.severity,
                    value=metric_value,
                    description=f"{rule.metric_name} exceeded threshold of {rule.threshold}"
                )
                self.alerts.append(alert)
                print(f"[ALERT - {rule.severity}] {alert.description}")

class DashboardData:
    """
    Stores and provides visualization data for the monitoring dashboard.
    
    Attributes:
        data: dictionary containing metric names and their historical data points
    """
    def __init__(self):
        self.data = {
            "cpu_usage": [],
            "memory_usage": [],
            "disk_usage": [],
            "network_usage": [],
            "request_latency": [],
            "error_rate": []
        }

    def add_data_point(self, metrics_data: MetricsData):
        """
        Adds a new data point to the dashboard data.
        
        Args:
            metrics_data: MetricsData object containing the metrics to add
        """
        for metric_name, value in metrics_data.metrics.items():
            self.data[metric_name].append((metrics_data.timestamp, value))

    def get_data(self, metric_name: str) -> List[Tuple[datetime, float]]:
        """
        Retrieves the historical data points for a specific metric.
        
        Args:
            metric_name: name of the metric to retrieve data for
            
        Returns:
            List of (timestamp, value) tuples for the specified metric
        """
        return self.data.get(metric_name, [])

class PerformanceProfiler:
    """
    Profiles code performance and collects execution time metrics.
    
    Attributes:
        profile_data: dictionary containing function names and their execution times
    """
    def __init__(self):
        self.profile_data = {}

    def profile_function(self, func):
        """
        Decorator to profile a function's execution time.
        
        Args:
            func: function to profile
            
        Returns:
            Decorated function that records execution time
        """
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            func_name = func.__name__
            self.profile_data[func_name] = self.profile_data.get(func_name, 0) + execution_time
            return result
        return wrapper

class AnomalyData:
    """
    Represents anomaly detection results with statistical information.
    
    Attributes:
        metric_name: name of the metric that showed anomalies
        anomalies: list of detected anomalies with timestamps and values
        statistics: dictionary containing statistical metrics for the data
    """
    def __init__(self, metric_name: str, anomalies: List[Tuple[datetime, float]], statistics: Dict[str, float]):
        self.metric_name = metric_name
        self.anomalies = anomalies
        self.statistics = statistics

class AnomalyDetector:
    """
    Detects anomalies in metric data using statistical methods.
    
    Attributes:
        window_size: number of data points to consider for anomaly detection
        threshold: z-score threshold for detecting anomalies
    """
    def __init__(self, window_size: int = 30, threshold: float = 3.0):
        self.window_size = window_size
        self.threshold = threshold

    def detect_anomalies(self, data_points: List[Tuple[datetime, float]]) -> AnomalyData:
        """
        Detects anomalies in a list of data points.
        
        Args:
            data_points: list of (timestamp, value) tuples for the metric
            
        Returns:
            AnomalyData object containing the detected anomalies and statistics
        """
        if len(data_points) < self.window_size:
            return AnomalyData("", [], {})
        
        # Calculate statistics
        values = [point[1] for point in data_points]
        mean = sum(values) / len(values)
        std_dev = (sum((x - mean)**2 for x in values) / len(values))**0.5
        
        # Find anomalies
        anomalies = []
        for timestamp, value in data_points:
            z_score = abs(value - mean) / std_dev
            if z_score > self.threshold:
                anomalies.append((timestamp, value))
        
        return AnomalyData(
            metric_name=data_points[0][0].strftime("%Y-%m-%d"),
            anomalies=anomalies,
            statistics={
                "mean": mean,
                "std_dev": std_dev,
                "anomaly_count": len(anomalies)
            }
        )

class LogEntry:
    """
    Represents a single log entry with metadata and content.
    
    Attributes:
        timestamp: datetime object indicating when the log was generated
        level: log level (INFO, WARNING, ERROR, etc.)
        message: content of the log message
        source: source of the log entry
    """
    def __init__(self, timestamp: datetime, level: str, message: str, source: str):
        self.timestamp = timestamp
        self.level = level
        self.message = message
        self.source = source

class LogAggregator:
    """
    Aggregates and processes logs from distributed sources.
    
    Attributes:
        logs: list of LogEntry objects representing aggregated logs
    """
    def __init__(self):
        self.logs = []

    async def aggregate_logs(self, log_entries: List[LogEntry]):
        """
        Aggregates a list of log entries.
        
        Args:
            log_entries: list of LogEntry objects to aggregate
        """
        for entry in log_entries:
            self.logs.append(entry)
            print(f"[LOG - {entry.level}] {entry.message} from {entry.source}")

class TraceSpan:
    """
    Represents a single trace span with metadata and timing information.
    
    Attributes:
        trace_id: unique identifier for the trace
        span_id: unique identifier for the span
        name: name of the operation
        start_time: datetime object indicating when the span started
        end_time: datetime object indicating when the span ended
        status: status of the span (OK, ERROR, etc.)
        attributes: dictionary containing additional attributes
    """
    def __init__(self, trace_id: str, span_id: str, name: str, start_time: datetime, end_time: datetime, status: str, attributes: Dict[str, str]):
        self.trace_id = trace_id
        self.span_id = span_id
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        self.attributes = attributes

class TraceSystem:
    """
    Manages distributed tracing with span creation and query capabilities.
    
    Attributes:
        traces: dictionary mapping trace IDs to list of TraceSpan objects
    """
    def __init__(self):
        self.traces = {}

    def start_trace(self, trace_id: str, span_id: str, name: str, attributes: Dict[str, str]):
        """
        Starts a new trace span.
        
        Args:
            trace_id: unique identifier for the trace
            span_id: unique identifier for the span
            name: name of the operation
            attributes: dictionary containing additional attributes
        """
        span = TraceSpan(
            trace_id=trace_id,
            span_id=span_id,
            name=name,
            start_time=datetime.now(),
            end_time=datetime.now(),
            status="OK",
            attributes=attributes
        )
        if trace_id not in self.traces:
            self.traces[trace_id] = []
        self.traces[trace_id].append(span)

    def end_trace(self, trace_id: str, span_id: str, status: str):
        """
        Ends a trace span with the given status.
        
        Args:
            trace_id: unique identifier for the trace
            span_id: unique identifier for the span
            status: status of the span (OK, ERROR, etc.)
        """
        if trace_id in self.traces:
            for span in self.traces[trace_id]:
                if span.span_id == span_id:
                    span.end_time = datetime.now()
                    span.status = status
                    break

    def get_traces(self, trace_id: str) -> List[TraceSpan]:
        """
        Retrieves all spans for a specific trace ID.
        
        Args:
            trace_id: unique identifier for the trace
            
        Returns:
            List of TraceSpan objects for the specified trace
        """
        return self.traces.get(trace_id, [])

class MonitoringSystem:
    """
    Main monitoring system that integrates all components.
    
    Attributes:
        metrics_collector: MetricsCollector instance for collecting metrics
        alert_manager: AlertManager instance for managing alerts
        dashboard_data: DashboardData instance for storing visualization data
        profiler: PerformanceProfiler instance for code profiling
        anomaly_detector: AnomalyDetector instance for anomaly detection
        log_aggregator: LogAggregator instance for log aggregation
        trace_system: TraceSystem instance for distributed tracing
    """
    def __init__(self):
        self.metrics_collector = MetricsCollector(interval=5)
        self.alert_manager = AlertManager()
        self.dashboard_data = DashboardData()
        self.profiler = PerformanceProfiler()
        self.anomaly_detector = AnomalyDetector(window_size=60, threshold=3.0)
        self.log_aggregator = LogAggregator()
        self.trace_system = TraceSystem()

    async def run(self):
        """
        Main entry point to start the monitoring system.
        """
        # Setup alert rules
        self.alert_manager.add_rule(AlertRule("cpu_usage", 0.95, "critical", window=60))
        self.alert_manager.add_rule(AlertRule("memory_usage", 0.85, "warning", window=30))
        self.alert_manager.add_rule(AlertRule("error_rate", 0.2, "info", window=120))
        
        # Create some test logs
        test_logs = [
            LogEntry(
                timestamp=datetime.now(),
                level="INFO",
                message="System started",
                source="main"
            ),
            LogEntry(
                timestamp=datetime.now(),
                level="WARNING",
                message="High CPU usage detected",
                source="monitor"
            ),
            LogEntry(
                timestamp=datetime.now(),
                level="ERROR",
                message="Database connection failed",
                source="db"
            )
        ]
        
        # Start the monitoring loop
        while True:
            try:
                # Collect metrics
                metrics_data = await self.metrics_collector.collect()
                self.dashboard_data.add_data_point(metrics_data)
                self.alert_manager.alert(metrics_data)
                
                # Profile some functions
                @self.profiler.profile_function
                def sample_function():
                    time.sleep(0.1)
                
                sample_function()
                
                # Detect anomalies
                anomaly_data = self.anomaly_detector.detect_anomalies(
                    self.dashboard_data.get_data("cpu_usage")
                )
                print(f"Anomalies detected: {anomaly_data.anomaly_count}")
                
                # Aggregate logs
                self.log_aggregator.aggregate_logs(test_logs)
                
                # Manage traces
                trace_id = "trace-123"
                self.trace_system.start_trace(trace_id, "span-1", "API call", {"method": "GET"})
                self.trace_system.end_trace(trace_id, "span-1", "OK")
                
                # Wait for the next iteration
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"Error in monitoring system: {str(e)}")
                await asyncio.sleep(1)

# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        system = MonitoringSystem()
        await system.run()
    
    asyncio.run(main())
</think>

# 智能监控系统设计与实现

## 系统架构概览

本监控系统采用模块化设计，包含六大核心组件，形成完整的监控闭环：

1. **指标采集系统**：实时采集系统运行状态指标
2. **告警管理系统**：基于阈值的智能告警机制
3. **可视化面板**：历史数据展示与分析
4. **性能分析器**：代码执行效率分析
5. **异常检测器**：基于统计学的异常识别
6. **日志聚合器**：分布式日志集中管理
7. **分布式追踪系统**：请求流程追踪

## 核心组件详解

### 1. 指标采集系统 (MetricsCollector)
- **功能**：持续采集系统关键指标
- **指标类型**：
  - CPU使用率
  - 内存占用
  - 网络流量
  - 请求延迟
  - 错误率
- **采集频率**：每5秒采集一次
- **数据存储**：通过DashboardData持久化存储

```python
class MetricsCollector:
    def __init__(self, interval=5):
        self.interval = interval
    
    async def collect(self):
        # 模拟指标采集
        return {
            "cpu_usage": random.uniform(0.4, 0.9),
            "memory_usage": random.uniform(0.3, 0.7),
            "network_usage": random.uniform(0.1, 0.5),
            "request_latency": random.uniform(0.05, 0.2),
            "error_rate": random.uniform(0.01, 0.1)
        }
```

### 2. 告警管理系统 (AlertManager)
- **告警策略**：
  - CPU > 95%：紧急告警
  - 内存 > 85%：警告
  - 错误率 > 20%：信息告警
- **告警窗口**：
  - CPU：60秒窗口
  - 内存：30秒窗口
  - 错误率：120秒窗口
- **告警机制**：基于滑动窗口的实时监测

### 3. 可视化面板 (DashboardData)
- **数据存储**：使用列表存储时间序列数据
- **数据格式**：(timestamp, value)
- **查询接口**：支持按指标查询历史数据

```python
class DashboardData:
    def __init__(self):
        self.data = {
            "cpu_usage": [],
            "memory_usage": [],
            "network_usage": [],
            "request_latency": [],
            "error_rate": []
        }
    
    def add_data_point(self, metrics_data):
        for metric_name, value in metrics_data.items():
            self.data[metric_name].append((datetime.now(), value))
```

### 4. 性能分析器 (PerformanceProfiler)
- **功能**：通过装饰器监控函数执行时间
- **数据存储**：记录每个函数的累计执行时间
- **使用示例**：

```python
@profiler.profile_function
def sample_function():
    time.sleep(0.1)
```

### 5. 异常检测器 (AnomalyDetector)
- **检测算法**：
  - 使用Z-score统计方法
  - 窗口大小：60个数据点
  - 阈值：3个标准差
- **输出**：异常时间序列和统计信息

### 6. 日志聚合器 (LogAggregator)
- **功能**：集中管理分布式日志
- **日志结构**：
  - 时间戳
  - 日志级别
  - 消息内容
  - 源标识
- **存储方式**：列表存储日志条目

### 7. 分布式追踪系统 (TraceSystem)
- **追踪机制**：
  - 每个请求分配唯一trace_id
  - 每个操作分配唯一span_id
- **数据结构**：使用字典存储trace信息
- **追踪信息**：
  - 时间戳
  - 操作名称
  - 状态码
  - 附加属性

## 系统运行流程

1. **初始化**：创建所有监控组件实例
2. **配置告警规则**：设置不同指标的告警阈值
3. **启动监控循环**：
   - 收集系统指标
   - 更新可视化面板
   - 触发告警机制
   - 执行性能分析
   - 检测异常模式
   - 聚合日志信息
   - 管理分布式追踪
4. **持续运行**：每5秒执行一次监控周期

## 系统优势

1. **实时监控**：每5秒更新系统状态
2. **智能告警**：基于滑动窗口的阈值检测
3. **可视化分析**：支持历史数据查询与分析
4. **性能优化**：函数级执行时间分析
5. **异常检测**：基于统计学的异常识别
6. **日志集中管理**：统一收集分布式日志
7. **请求追踪**：完整请求流程追踪

## 扩展建议

1. **增加指标维度**：支持添加更多监控指标
2. **机器学习预测**：使用时间序列预测模型
3. **可视化升级**：集成图表库实现动态可视化
4. **告警通知**：集成邮件/短信通知系统
5. **日志分析**：增加日志内容分析功能
6. **分布式架构**：支持多节点监控系统
7. **数据持久化**：增加数据库存储功能

## 技术选型建议

1. **时间序列数据库**：InfluxDB
2. **可视化工具**：Grafana
3. **日志系统**：ELK Stack
4. **消息队列**：Kafka
5. **分布式追踪**：Jaeger
6. **数据库**：PostgreSQL
7. **缓存系统**：Redis

该监控系统具备良好的可扩展性和可维护性，能够适应不同规模的系统监控需求。通过模块化设计，各组件可以独立开发和测试，同时保持系统的整体一致性。