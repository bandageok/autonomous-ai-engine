"""Tools Executor - 工具执行器"""
import asyncio
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class ExecutionResult:
    """执行结果"""
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration: float = 0.0

class ToolsExecutor:
    """工具执行器"""
    
    def __init__(self, registry):
        self.registry = registry
        self.execution_history: List[ExecutionResult] = []
        
    async def execute(self, tool_name: str, **kwargs) -> ExecutionResult:
        """执行工具"""
        start_time = datetime.now()
        
        tool = self.registry.get(tool_name)
        if not tool:
            return ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=f"Tool not found: {tool_name}"
            )
            
        try:
            func = tool.func
            
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
                
            duration = (datetime.now() - start_time).total_seconds()
            
            exec_result = ExecutionResult(
                tool_name=tool_name,
                success=True,
                result=result,
                duration=duration
            )
            
            self.execution_history.append(exec_result)
            return exec_result
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            
            exec_result = ExecutionResult(
                tool_name=tool_name,
                success=False,
                result=None,
                error=str(e),
                duration=duration
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
        if not self.execution_history:
            return {}
            
        total = len(self.execution_history)
        success = sum(1 for r in self.execution_history if r.success)
        
        return {
            "total": total,
            "success": success,
            "failed": total - success,
            "success_rate": success / total if total > 0 else 0
        }
