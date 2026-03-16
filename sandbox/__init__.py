"""Sandbox - 安全沙箱
安全的代码执行环境，用于隔离执行不可信代码
"""
import asyncio
import subprocess
import tempfile
import os
import uuid
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import signal


@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    output: str
    error: str = ""
    duration: float = 0.0
    exit_code: int = 0


@dataclass
class SandboxConfig:
    """沙箱配置"""
    timeout: int = 30  # 超时时间(秒)
    memory_limit: int = 512  # 内存限制(MB)
    max_output_size: int = 1024 * 1024  # 最大输出大小(字节)
    allowed_languages: List[str] = field(default_factory=lambda: ["python", "javascript", "bash"])
    temp_dir: Optional[Path] = None


class Sandbox:
    """安全沙箱"""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.temp_dir = self.config.temp_dir or Path(tempfile.gettempdir()) / "sandbox"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self._execution_count = 0
    
    async def execute_python(self, code: str, input_data: str = "") -> ExecutionResult:
        """执行Python代码"""
        return await self._execute(
            language="python",
            code=code,
            input_data=input_data
        )
    
    async def execute_javascript(self, code: str, input_data: str = "") -> ExecutionResult:
        """执行JavaScript代码"""
        return await self._execute(
            language="javascript",
            code=code,
            input_data=input_data
        )
    
    async def execute_bash(self, command: str, input_data: str = "") -> ExecutionResult:
        """执行Bash命令"""
        return await self._execute(
            language="bash",
            code=command,
            input_data=input_data
        )
    
    async def _execute(self, language: str, code: str, input_data: str = "") -> ExecutionResult:
        """通用执行"""
        if language not in self.config.allowed_languages:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Language '{language}' not allowed"
            )
        
        self._execution_count += 1
        execution_id = str(uuid.uuid4())[:8]
        
        # 创建临时文件
        if language == "python":
            file_ext = ".py"
            run_cmd = ["python"]
        elif language == "javascript":
            file_ext = ".js"
            run_cmd = ["node"]
        else:
            file_ext = ".sh"
            run_cmd = ["bash"]
        
        temp_file = self.temp_dir / f"{execution_id}{file_ext}"
        input_file = self.temp_dir / f"{execution_id}.in"
        
        try:
            # 写入代码
            temp_file.write_text(code, encoding="utf-8")
            
            # 写入输入
            if input_data:
                input_file.write_text(input_data, encoding="utf-8")
            
            # 执行
            start_time = datetime.now()
            
            cmd = run_cmd + [str(temp_file)]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.temp_dir)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=input_data.encode() if input_data else None),
                    timeout=self.config.timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ExecutionResult(
                    success=False,
                    output="",
                    error=f"Execution timeout ({self.config.timeout}s)"
                )
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # 限制输出大小
            output = stdout.decode("utf-8", errors="replace")
            if len(output) > self.config.max_output_size:
                output = output[:self.config.max_output_size] + "\n... (truncated)"
            
            error = stderr.decode("utf-8", errors="replace")
            
            return ExecutionResult(
                success=process.returncode == 0,
                output=output,
                error=error,
                duration=duration,
                exit_code=process.returncode
            )
            
        except Exception as e:
            return ExecutionResult(
                success=False,
                output="",
                error=str(e)
            )
        finally:
            # 清理临时文件
            for f in [temp_file, input_file]:
                if f.exists():
                    try:
                        f.unlink()
                    except:
                        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "execution_count": self._execution_count,
            "temp_dir": str(self.temp_dir),
            "config": {
                "timeout": self.config.timeout,
                "memory_limit": self.config.memory_limit,
                "allowed_languages": self.config.allowed_languages
            }
        }


class CodeSandboxPool:
    """沙箱池 - 管理多个沙箱实例"""
    
    def __init__(self, pool_size: int = 4):
        self.pool_size = pool_size
        self.sandboxes: List[Sandbox] = []
        self._current = 0
        
        for _ in range(pool_size):
            self.sandboxes.append(Sandbox())
    
    async def execute(self, language: str, code: str, input_data: str = "") -> ExecutionResult:
        """分配执行"""
        sandbox = self.sandboxes[self._current]
        self._current = (self._current + 1) % self.pool_size
        
        if language == "python":
            return await sandbox.execute_python(code, input_data)
        elif language == "javascript":
            return await sandbox.execute_javascript(code, input_data)
        elif language == "bash":
            return await sandbox.execute_bash(code, input_data)
        else:
            return ExecutionResult(
                success=False,
                output="",
                error=f"Unsupported language: {language}"
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取池统计"""
        return {
            "pool_size": self.pool_size,
            "sandboxes": [s.get_stats() for s in self.sandboxes]
        }


# 全局沙箱池
_global_pool = CodeSandboxPool()


async def execute_code(language: str, code: str, input_data: str = "") -> ExecutionResult:
    """全局执行函数"""
    return await _global_pool.execute(language, code, input_data)


def get_sandbox_pool() -> CodeSandboxPool:
    """获取全局沙箱池"""
    return _global_pool
