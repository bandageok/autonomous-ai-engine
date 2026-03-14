"""
Auto-Code Repair - 代码自修复系统
创新点：自动检测bug、分析错误、自动修复
"""
import ast
import re
import traceback
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import json

# ==================== 错误检测器 ====================

class ErrorDetector:
    """错误检测器"""
    
    def __init__(self):
        self.error_patterns: Dict[str, str] = {
            "syntax": r"SyntaxError: (.+)",
            "import": r"ImportError: (.+)",
            "attribute": r"AttributeError: (.+)",
            "type": r"TypeError: (.+)",
            "value": r"ValueError: (.+)",
            "index": r"IndexError: (.+)",
            "key": r"KeyError: (.+)",
            "runtime": r"RuntimeError: (.+)",
            "timeout": r"TimeoutError: (.+)"
        }
        
    def detect_from_exception(self, exc: Exception) -> Dict:
        """从异常检测错误类型"""
        exc_type = type(exc).__name__
        exc_msg = str(exc)
        
        # 匹配模式
        for error_type, pattern in self.error_patterns.items():
            match = re.search(pattern, exc_msg)
            if match:
                return {
                    "type": error_type,
                    "error": exc_type,
                    "message": match.group(1) if match else exc_msg,
                    "full_trace": traceback.format_exc()
                }
                
        return {
            "type": "unknown",
            "error": exc_type,
            "message": exc_msg,
            "full_trace": traceback.format_exc()
        }
        
    def detect_from_log(self, log: str) -> List[Dict]:
        """从日志检测错误"""
        errors = []
        
        for error_type, pattern in self.error_patterns.items():
            for match in re.finditer(pattern, log):
                errors.append({
                    "type": error_type,
                    "message": match.group(1),
                    "position": match.start()
                })
                
        return errors


# ==================== 静态分析器 ====================

class StaticAnalyzer:
    """静态分析器 - 不运行代码检测问题"""
    
    def __init__(self):
        self.issues: List[Dict] = []
        
    def analyze_file(self, file_path: Path) -> Dict:
        """分析文件"""
        if not file_path.exists():
            return {"error": "File not found"}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                
            tree = ast.parse(source)
            
            return {
                "file": str(file_path),
                "issues": self._analyze_tree(tree, source),
                "metrics": self._calculate_metrics(tree, source)
            }
            
        except SyntaxError as e:
            return {
                "file": str(file_path),
                "syntax_error": {
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text
                }
            }
            
    def _analyze_tree(self, tree: ast.AST, source: str) -> List[Dict]:
        """分析AST树"""
        issues = []
        
        for node in ast.walk(tree):
            # 检测空except块
            if isinstance(node, ast.ExceptHandler):
                if node.type is None and node.body:
                    issues.append({
                        "severity": "warning",
                        "type": "bare_except",
                        "line": node.lineno,
                        "message": "Bare except clause may catch unexpected errors"
                    })
                    
            # 检测可变默认参数
            if isinstance(node, ast.FunctionDef):
                for arg in node.args.defaults:
                    if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            "severity": "error",
                            "type": "mutable_default",
                            "line": node.lineno,
                            "message": "Mutable default argument may cause unexpected behavior"
                        })
                        
            # 检测未使用的变量
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                # 简化检测
                pass
                
        return issues
        
    def _calculate_metrics(self, tree: ast.AST, source: str) -> Dict:
        """计算代码度量"""
        lines = source.split('\n')
        
        return {
            "lines": len(lines),
            "code_lines": len([l for l in lines if l.strip() and not l.strip().startswith('#')]),
            "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
            "blank_lines": len([l for l in lines if not l.strip()]),
            "functions": sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef)),
            "classes": sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef)),
            "imports": sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.Import, ast.ImportFrom)))
        }


# ==================== 代码修复器 ====================

class CodeFixer:
    """代码修复器"""
    
    def __init__(self):
        self.fixes: Dict[str, Callable] = {
            "mutable_default": self._fix_mutable_default,
            "bare_except": self._fix_bare_except,
            "unused_import": self._fix_unused_import,
            "missing_return": self._fix_missing_return
        }
        
    def fix_issue(self, issue: Dict, file_path: Path) -> bool:
        """修复问题"""
        issue_type = issue.get("type")
        
        fixer = self.fixes.get(issue_type)
        if not fixer:
            return False
            
        try:
            return fixer(issue, file_path)
        except Exception as e:
            print(f"Fix failed: {e}")
            return False
            
    def _fix_mutable_default(self, issue: Dict, file_path: Path) -> bool:
        """修复可变默认参数"""
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        # 找到问题行并修复
        line_num = issue.get("line", 0) - 1
        if 0 <= line_num < len(lines):
            # 简单修复：将[]改为None
            line = lines[line_num]
            if "= []" in line:
                lines[line_num] = line.replace("= []", "= None")
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            return True
            
        return False
        
    def _fix_bare_except(self, issue: Dict, file_path: Path) -> bool:
        """修复空except"""
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        line_num = issue.get("line", 0) - 1
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            # 添加具体异常类型
            if "except:" in line:
                lines[line_num] = line.replace("except:", "except Exception:")
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            return True
            
        return False
        
    def _fix_unused_import(self, issue: Dict, file_path: Path) -> bool:
        """修复未使用导入"""
        # 简化实现
        return False
        
    def _fix_missing_return(self, issue: Dict, file_path: Path) -> bool:
        """修复缺失返回"""
        return False


# ==================== 运行时监控 ====================

class RuntimeMonitor:
    """运行时监控"""
    
    def __init__(self):
        self.errors: List[Dict] = []
        self.performance: Dict = {}
        
    def watch_function(self, func: Callable) -> Callable:
        """监控函数"""
        import functools
        import time
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                    
                duration = time.time() - start_time
                self._record_success(func.__name__, duration)
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                self._record_error(func.__name__, e, duration)
                raise
                
        return wrapper
        
    def _record_success(self, func_name: str, duration: float):
        """记录成功"""
        if func_name not in self.performance:
            self.performance[func_name] = {
                "calls": 0,
                "total_time": 0,
                "errors": 0
            }
            
        self.performance[func_name]["calls"] += 1
        self.performance[func_name]["total_time"] += duration
        
    def _record_error(self, func_name: str, error: Exception, duration: float):
        """记录错误"""
        self.errors.append({
            "function": func_name,
            "error": str(error),
            "type": type(error).__name__,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        })
        
        if func_name in self.performance:
            self.performance[func_name]["errors"] += 1
            
    def get_error_summary(self) -> Dict:
        """获取错误摘要"""
        error_counts = {}
        
        for error in self.errors:
            err_type = error["type"]
            error_counts[err_type] = error_counts.get(err_type, 0) + 1
            
        return {
            "total_errors": len(self.errors),
            "by_type": error_counts,
            "recent_errors": self.errors[-10:]
        }
        
    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        summary = {}
        
        for func_name, stats in self.performance.items():
            avg_time = stats["total_time"] / max(stats["calls"], 1)
            error_rate = stats["errors"] / max(stats["calls"], 1)
            
            summary[func_name] = {
                "calls": stats["calls"],
                "avg_time_ms": avg_time * 1000,
                "errors": stats["errors"],
                "error_rate": error_rate
            }
            
        return summary


import asyncio

# ==================== 自修复引擎 ====================

class AutoRepairEngine:
    """自修复引擎"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.error_detector = ErrorDetector()
        self.static_analyzer = StaticAnalyzer()
        self.code_fixer = CodeFixer()
        self.runtime_monitor = RuntimeMonitor()
        self.repair_history: List[Dict] = []
        
    async def analyze_and_fix(self, file_path: Path = None) -> Dict:
        """分析并修复"""
        results = {
            "files_analyzed": 0,
            "issues_found": 0,
            "issues_fixed": 0,
            "fixes_failed": 0,
            "details": []
        }
        
        # 确定要分析的文件
        files_to_analyze = []
        
        if file_path:
            files_to_analyze = [file_path]
        else:
            files_to_analyze = list(self.project_path.rglob("*.py"))
            
        for py_file in files_to_analyze:
            if "__pycache__" in str(py_file):
                continue
                
            results["files_analyzed"] += 1
            
            # 静态分析
            analysis = self.static_analyzer.analyze_file(py_file)
            
            if analysis.get("issues"):
                results["issues_found"] += len(analysis["issues"])
                
                for issue in analysis["issues"]:
                    # 尝试修复
                    fixed = self.code_fixer.fix_issue(issue, py_file)
                    
                    if fixed:
                        results["issues_fixed"] += 1
                        results["details"].append({
                            "file": str(py_file),
                            "issue": issue,
                            "status": "fixed"
                        })
                    else:
                        results["fixes_failed"] += 1
                        
        # 记录历史
        self.repair_history.append({
            "timestamp": datetime.now().isoformat(),
            "results": results
        })
        
        return results
        
    def repair_from_error(self, error: Exception, context: Dict) -> Dict:
        """从错误修复"""
        # 检测错误类型
        error_info = self.error_detector.detect_from_exception(error)
        
        # 记录错误
        self.repair_history.append({
            "timestamp": datetime.now().isoformat(),
            "error": error_info,
            "context": context,
            "status": "detected"
        })
        
        # 生成修复建议
        suggestions = self._generate_fix_suggestions(error_info)
        
        return {
            "error": error_info,
            "suggestions": suggestions
        }
        
    def _generate_fix_suggestions(self, error_info: Dict) -> List[str]:
        """生成修复建议"""
        error_type = error_info.get("type")
        message = error_info.get("message", "")
        
        suggestions = []
        
        if error_type == "syntax":
            suggestions.append("检查语法错误，可能是缺少冒号、括号不匹配等")
        elif error_type == "import":
            suggestions.append("检查模块是否正确安装，或使用try-except处理导入")
        elif error_type == "attribute":
            suggestions.append("检查属性是否存在，或对象类型是否正确")
        elif error_type == "type":
            suggestions.append("检查变量类型是否匹配，或进行类型转换")
        elif error_type == "value":
            suggestions.append("检查值是否有效，或添加验证")
        elif error_type == "index":
            suggestions.append("检查索引是否越界，或添加边界检查")
        elif error_type == "key":
            suggestions.append("检查键是否存在，或使用get方法提供默认值")
            
        return suggestions
        
    def get_repair_stats(self) -> Dict:
        """获取修复统计"""
        total_fixes = len([h for h in self.repair_history if h.get("status") == "fixed"])
        
        return {
            "total_repairs": len(self.repair_history),
            "fixed": total_fixes,
            "detected": len(self.repair_history) - total_fixes,
            "recent_repairs": self.repair_history[-10:]
        }


# ==================== 使用示例 ====================

async def main():
    """使用示例"""
    from pathlib import Path
    
    project = Path("autonomous-ai-engine")
    engine = AutoRepairEngine(project)
    
    # 静态分析
    print("Running static analysis...")
    results = await engine.analyze_and_fix()
    
    print(f"\nAnalysis Results:")
    print(f"  Files analyzed: {results['files_analyzed']}")
    print(f"  Issues found: {results['issues_found']}")
    print(f"  Issues fixed: {results['issues_fixed']}")
    print(f"  Fixes failed: {results['fixes_failed']}")
    
    # 获取统计
    stats = engine.get_repair_stats()
    print(f"\nRepair Stats:")
    print(f"  Total repairs: {stats['total_repairs']}")
    

if __name__ == "__main__":
    asyncio.run(main())
