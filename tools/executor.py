"""Tools Executor - 工具执行器 + 高级工具执行系统"""
import asyncio
import hashlib
import logging
import time
import uuid
from typing import Dict, List, Any, Callable, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class Permission(Enum):
    """工具权限级别"""
    PUBLIC = "public"
    RESTRICTED = "restricted"
    ADMIN = "admin"
    SYSTEM = "system"

@dataclass
class ExecutionResult:
    """执行结果"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration: float = 0.0
    execution_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)

@dataclass
class ToolVersion:
    """工具版本"""
    version: str
    func: Callable
    created_at: datetime = field(default_factory=datetime.now)
    changelog: str = ""

@dataclass
class ToolDependency:
    """工具依赖"""
    name: str
    version_constraint: str  # 例如: ">=1.0.0"
    optional: bool = False

@dataclass
class ToolDefinition:
    """工具定义"""
    name: str
    func: Callable
    version: str
    description: str = ""
    permission: Permission = Permission.PUBLIC
    timeout: int = 30
    cache_ttl: int = 0  # 缓存TTL，0表示不缓存
    dependencies: List[ToolDependency] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    author: str = ""
    validate_input: Optional[Callable] = None
    validate_output: Optional[Callable] = None
    version_history: List[ToolVersion] = field(default_factory=list)
    
    def __post_init__(self):
        # 初始化版本历史
        if not self.version_history:
            self.version_history.append(ToolVersion(
                version=self.version,
                func=self.func,
                changelog="Initial version"
            ))

class ExecutionCache:
    """执行结果缓存"""
    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.cache: Dict[str, tuple] = {}  # (result, expiry)
    
    def _generate_key(self, tool_name: str, **kwargs) -> str:
        """生成缓存键"""
        key_data = f"{tool_name}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, tool_name: str, **kwargs) -> Optional[Any]:
        """获取缓存"""
        key = self._generate_key(tool_name, **kwargs)
        if key in self.cache:
            result, expiry = self.cache[key]
            if datetime.now() < expiry:
                logger.debug(f"Cache hit for {tool_name}")
                return result
            else:
                del self.cache[key]
        return None
    
    def set(self, tool_name: str, result: Any, ttl: int = None):
        """设置缓存"""
        key = self._generate_key(tool_name, **{})
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (result, expiry)
        logger.debug(f"Cached result for {tool_name} (TTL: {ttl}s)")
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        logger.info("Execution cache cleared")

class ExecutionAudit:
    """执行审计日志"""
    def __init__(self):
        self.audit_log: List[Dict] = []
        self.max_entries: int = 10000
    
    def log_execution(
        self,
        execution_id: str,
        tool_name: str,
        status: ExecutionStatus,
        user: str = "system",
        duration: float = 0.0,
        input_params: Dict = None,
        result: Any = None,
        error: str = None
    ):
        """记录执行"""
        entry = {
            'execution_id': execution_id,
            'tool_name': tool_name,
            'status': status.value,
            'user': user,
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'input_params': input_params or {},
            'result_preview': str(result)[:100] if result else None,
            'error': error
        }
        
        self.audit_log.append(entry)
        
        # 限制日志大小
        if len(self.audit_log) > self.max_entries:
            self.audit_log = self.audit_log[-self.max_entries:]
    
    def get_logs(
        self,
        tool_name: str = None,
        status: ExecutionStatus = None,
        user: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """查询审计日志"""
        logs = self.audit_log
        
        if tool_name:
            logs = [l for l in logs if l['tool_name'] == tool_name]
        if status:
            logs = [l for l in logs if l['status'] == status.value]
        if user:
            logs = [l for l in logs if l['user'] == user]
        
        return logs[-limit:]

class SandboxExecutor:
    """沙箱执行器"""
    def __init__(self, max_memory_mb: int = 256, max_cpu_percent: int = 50):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.allowed_modules: Set[str] = set()
        self.blocked_modules: Set[str] = set()
        self._initialize_sandbox()
    
    def _initialize_sandbox(self):
        """初始化沙箱"""
        # 默认允许的基础模块
        self.allowed_modules = {
            'math', 'random', 'json', 'datetime', 'time',
            're', 'collections', 'itertools', 'functools'
        }
        logger.info("Sandbox executor initialized")
    
    def add_allowed_module(self, module: str):
        """添加允许的模块"""
        self.allowed_modules.add(module)
    
    def add_blocked_module(self, module: str):
        """添加阻止的模块"""
        self.blocked_modules.add(module)
    
    def execute_in_sandbox(self, func: Callable, **kwargs) -> Any:
        """在沙箱中执行"""
        # 简化的沙箱实现
        # 实际生产中应使用真正的沙箱技术如Docker
        try:
            return func(**kwargs)
        except Exception as e:
            logger.error(f"Sandbox execution error: {e}")
            raise

class PermissionChecker:
    """权限检查器"""
    def __init__(self):
        self.user_permissions: Dict[str, Set[Permission]] = {}
        self.tool_permissions: Dict[str, Permission] = {}
    
    def set_user_permission(self, user: str, permissions: Set[Permission]):
        """设置用户权限"""
        self.user_permissions[user] = permissions
    
    def set_tool_permission(self, tool_name: str, permission: Permission):
        """设置工具权限"""
        self.tool_permissions[tool_name] = permission
    
    def check_permission(self, user: str, tool_name: str) -> bool:
        """检查权限"""
        tool_perm = self.tool_permissions.get(tool_name, Permission.PUBLIC)
        
        if tool_perm == Permission.PUBLIC:
            return True
        
        user_perms = self.user_permissions.get(user, set())
        return tool_perm in user_perms

class ResultValidator:
    """结果验证器"""
    def __init__(self):
        self.validators: Dict[str, Callable] = {}
    
    def register_validator(self, tool_name: str, validator: Callable):
        """注册验证器"""
        self.validators[tool_name] = validator
    
    def validate(self, tool_name: str, result: Any) -> bool:
        """验证结果"""
        if tool_name not in self.validators:
            return True  # 没有验证器则默认通过
        
        try:
            return self.validators[tool_name](result)
        except Exception as e:
            logger.error(f"Validation error for {tool_name}: {e}")
            return False

class ExecutionStatistics:
    """执行统计"""
    def __init__(self):
        self.stats: Dict[str, Dict] = {}
    
    def record_execution(self, tool_name: str, duration: float, success: bool):
        """记录执行"""
        if tool_name not in self.stats:
            self.stats[tool_name] = {
                'total_calls': 0,
                'total_duration': 0.0,
                'success_count': 0,
                'failure_count': 0,
                'avg_duration': 0.0
            }
        
        stat = self.stats[tool_name]
        stat['total_calls'] += 1
        stat['total_duration'] += duration
        
        if success:
            stat['success_count'] += 1
        else:
            stat['failure_count'] += 1
        
        stat['avg_duration'] = stat['total_duration'] / stat['total_calls']
    
    def get_stats(self, tool_name: str = None) -> Dict:
        """获取统计"""
        if tool_name:
            return self.stats.get(tool_name, {})
        return {
            name: {
                'total_calls': s['total_calls'],
                'success_rate': s['success_count'] / s['total_calls'] if s['total_calls'] > 0 else 0,
                'avg_duration': s['avg_duration']
            }
            for name, s in self.stats.items()
        }

class AdvancedToolsExecutor:
    """高级工具执行器 - 支持版本管理、依赖解析、沙箱执行、权限控制、缓存、审计"""
    
    def __init__(self, registry):
        self.registry = registry
        self.execution_history: List[ExecutionResult] = []
        self.cache = ExecutionCache()
        self.audit = ExecutionAudit()
        self.sandbox = SandboxExecutor()
        self.permission_checker = PermissionChecker()
        self.validator = ResultValidator()
        self.statistics = ExecutionStatistics()
        self.current_user: str = "system"
        self._tool_versions: Dict[str, Dict[str, ToolVersion]] = {}  # tool_name -> {version: ToolVersion}
    
    def set_current_user(self, user: str):
        """设置当前用户"""
        self.current_user = user
    
    def register_tool_version(
        self,
        tool_name: str,
        version: str,
        func: Callable,
        changelog: str = ""
    ):
        """注册工具版本"""
        if tool_name not in self._tool_versions:
            self._tool_versions[tool_name] = {}
        
        self._tool_versions[tool_name][version] = ToolVersion(
            version=version,
            func=func,
            changelog=changelog
        )
        logger.info(f"Registered version {version} for tool {tool_name}")
    
    def get_tool_version(self, tool_name: str, version: str = None) -> Optional[Callable]:
        """获取工具版本"""
        if tool_name not in self._tool_versions:
            return None
        
        versions = self._tool_versions[tool_name]
        
        if version:
            tool_version = versions.get(version)
            return tool_version.func if tool_version else None
        
        # 返回最新版本
        if versions:
            latest = max(versions.items(), key=lambda x: x[1].created_at)
            return latest[1].func
        return None
    
    def resolve_dependencies(self, tool_name: str) -> List[str]:
        """解析工具依赖"""
        tool = self.registry.get(tool_name)
        if not tool or not hasattr(tool, 'dependencies'):
            return []
        
        resolved = []
        for dep in tool.dependencies:
            if not self.registry.get(dep.name):
                if not dep.optional:
                    logger.warning(f"Missing required dependency: {dep.name}")
                continue
            resolved.append(dep.name)
        
        return resolved
    
    async def execute(
        self,
        tool_name: str,
        use_cache: bool = True,
        use_sandbox: bool = False,
        validate_result: bool = True,
        **kwargs
    ) -> ExecutionResult:
        """执行工具"""
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        # 权限检查
        if not self.permission_checker.check_permission(self.current_user, tool_name):
            error = f"Permission denied for tool: {tool_name}"
            logger.warning(error)
            result = ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=error,
                execution_id=execution_id
            )
            self.execution_history.append(result)
            return result
        
        # 缓存检查
        if use_cache:
            cached_result = self.cache.get(tool_name, **kwargs)
            if cached_result is not None:
                logger.debug(f"Using cached result for {tool_name}")
                return ExecutionResult(
                    tool_name=tool_name,
                    success=True,
                    result=cached_result,
                    execution_id=execution_id,
                    metadata={'cached': True}
                )
        
        # 获取工具
        tool = self.registry.get(tool_name)
        if not tool:
            error = f"Tool not found: {tool_name}"
            result = ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=error,
                execution_id=execution_id
            )
            self.execution_history.append(result)
            return result
        
        # 依赖解析
        dependencies = self.resolve_dependencies(tool_name)
        logger.debug(f"Dependencies for {tool_name}: {dependencies}")
        
        # 执行
        try:
            func = tool.func if not use_sandbox else self.sandbox.execute_in_sandbox
            
            # 输入验证
            if hasattr(tool, 'validate_input') and tool.validate_input:
                tool.validate_input(**kwargs)
            
            # 执行并处理超时
            timeout = getattr(tool, 'timeout', 30)
            
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(func(**kwargs), timeout=timeout)
            else:
                result = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: func(**kwargs)
                )
            
            # 结果验证
            if validate_result and hasattr(tool, 'validate_output') and tool.validate_output:
                if not self.validator.validate(tool_name, result):
                    raise ValueError(f"Result validation failed for {tool_name}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            exec_result = ExecutionResult(
                tool_name=tool_name,
                success=True,
                result=result,
                duration=duration,
                execution_id=execution_id
            )
            
            # 缓存结果
            if use_cache and hasattr(tool, 'cache_ttl') and tool.cache_ttl > 0:
                self.cache.set(tool_name, result, tool.cache_ttl)
            
            # 记录统计
            self.statistics.record_execution(tool_name, duration, True)
            
            # 审计日志
            self.audit.log_execution(
                execution_id, tool_name, ExecutionStatus.COMPLETED,
                self.current_user, duration, kwargs, result
            )
            
            self.execution_history.append(exec_result)
            return exec_result
            
        except asyncio.TimeoutError:
            duration = (datetime.now() - start_time).total_seconds()
            error = f"Tool execution timed out after {timeout}s"
            
            exec_result = ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=error,
                duration=duration,
                execution_id=execution_id
            )
            
            self.statistics.record_execution(tool_name, duration, False)
            self.audit.log_execution(
                execution_id, tool_name, ExecutionStatus.TIMEOUT,
                self.current_user, duration, kwargs, error=error
            )
            
            self.execution_history.append(exec_result)
            return exec_result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error = str(e)
            
            exec_result = ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=error,
                duration=duration,
                execution_id=execution_id
            )
            
            self.statistics.record_execution(tool_name, duration, False)
            self.audit.log_execution(
                execution_id, tool_name, ExecutionStatus.FAILED,
                self.current_user, duration, kwargs, error=error
            )
            
            self.execution_history.append(exec_result)
            return exec_result
    
    def get_history(self, last_n: int = None) -> List[ExecutionResult]:
        """获取历史"""
        if last_n:
            return self.execution_history[-last_n:]
        return self.execution_history
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'executor': self.statistics.get_stats(),
            'cache': {
                'entries': len(self.cache.cache)
            },
            'audit': {
                'total_entries': len(self.audit.audit_log)
            }
        }

# 保持向后兼容
class ToolsExecutor(AdvancedToolsExecutor):
    """工具执行器 - 兼容旧版API"""
    pass
