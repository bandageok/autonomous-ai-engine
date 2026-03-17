"""Security Analyzer - 代码安全分析器
提供代码漏洞检测、危险函数识别和安全审计功能
"""
import ast
import re
import os
from typing import List, Dict, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import hashlib


class VulnerabilitySeverity(Enum):
    """漏洞严重等级"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """漏洞类型"""
    DANGEROUS_FUNCTION = "dangerous_function"
    SQL_INJECTION = "sql_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    HARDCODED_SECRET = "hardcoded_secret"
    XSS_VULNERABILITY = "xss"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    WEAK_CRYPTOGRAPHY = "weak_cryptography"
    UNSAFE_IMPORT = "unsafe_import"
    CODE_INJECTION = "code_injection"


@dataclass
class VulnerabilityFinding:
    """漏洞发现"""
    vuln_type: VulnerabilityType
    severity: VulnerabilitySeverity
    line_number: int
    column: int
    code_snippet: str
    description: str
    recommendation: str
    confidence: float = 1.0
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "type": self.vuln_type.value,
            "severity": self.severity.value,
            "line_number": self.line_number,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "description": self.description,
            "recommendation": self.recommendation,
            "confidence": self.confidence
        }


@dataclass
class VulnerabilityReport:
    """漏洞报告"""
    file_path: str
    total_lines: int
    findings: List[VulnerabilityFinding] = field(default_factory=list)
    scan_time: float = 0.0
    language: str = "python"
    
    @property
    def critical_count(self) -> int:
        """严重漏洞数量"""
        return sum(1 for f in findings if f.severity == VulnerabilitySeverity.CRITICAL)
    
    @property
    def high_count(self) -> int:
        """高危漏洞数量"""
        return sum(1 for f in findings if f.severity == VulnerabilitySeverity.HIGH)
    
    @property
    def medium_count(self) -> int:
        """中危漏洞数量"""
        return sum(1 for f in findings if f.severity == VulnerabilitySeverity.MEDIUM)
    
    @property
    def low_count(self) -> int:
        """低危漏洞数量"""
        return sum(1 for f in findings if f.severity == VulnerabilitySeverity.LOW)
    
    @property
    def risk_score(self) -> float:
        """风险评分 (0-100)"""
        weights = {
            VulnerabilitySeverity.CRITICAL: 10,
            VulnerabilitySeverity.HIGH: 5,
            VulnerabilitySeverity.MEDIUM: 2,
            VulnerabilitySeverity.LOW: 1,
            VulnerabilitySeverity.INFO: 0
        }
        return sum(weights[f.severity] for f in self.findings)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "file_path": self.file_path,
            "total_lines": self.total_lines,
            "findings": [f.to_dict() for f in self.findings],
            "scan_time": self.scan_time,
            "language": self.language,
            "summary": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "total": len(self.findings),
                "risk_score": self.risk_score
            }
        }


class DangerousFunction:
    """危险函数定义"""
    
    # 危险函数及其严重等级
    FUNCTIONS = {
        # 代码执行
        "eval": (VulnerabilitySeverity.CRITICAL, "动态代码执行"),
        "exec": (VulnerabilitySeverity.CRITICAL, "动态代码执行"),
        "compile": (VulnerabilitySeverity.HIGH, "动态代码编译"),
        "__import__": (VulnerabilitySeverity.HIGH, "动态模块导入"),
        
        # 命令执行
        "os.system": (VulnerabilitySeverity.CRITICAL, "Shell命令执行"),
        "os.popen": (VulnerabilitySeverity.CRITICAL, "Shell命令执行"),
        "subprocess.call": (VulnerabilitySeverity.HIGH, "子进程调用"),
        "subprocess.run": (VulnerabilitySeverity.HIGH, "子进程执行"),
        "subprocess.Popen": (VulnerabilitySeverity.CRITICAL, "子进程创建"),
        "subprocess.getoutput": (VulnerabilitySeverity.HIGH, "获取命令输出"),
        "subprocess.check_output": (VulnerabilitySeverity.HIGH, "获取命令输出"),
        "commands.getoutput": (VulnerabilitySeverity.HIGH, "获取命令输出"),
        "commands.getstatusoutput": (VulnerabilitySeverity.HIGH, "获取命令输出"),
        "os.popen": (VulnerabilitySeverity.CRITICAL, "管道打开"),
        "pty.spawn": (VulnerabilitySeverity.CRITICAL, "伪终端生成"),
        
        # 文件操作
        "open": (VulnerabilitySeverity.MEDIUM, "文件操作"),
        "file": (VulnerabilitySeverity.MEDIUM, "文件操作"),
        "os.remove": (VulnerabilitySeverity.MEDIUM, "文件删除"),
        "os.unlink": (VulnerabilitySeverity.MEDIUM, "文件删除"),
        "os.rmdir": (VulnerabilitySeverity.MEDIUM, "目录删除"),
        "shutil.rmtree": (VulnerabilitySeverity.HIGH, "目录树删除"),
        "shutil.move": (VulnerabilitySeverity.MEDIUM, "文件移动"),
        "shutil.copy": (VulnerabilitySeverity.MEDIUM, "文件复制"),
        
        # 序列化
        "pickle.load": (VulnerabilitySeverity.CRITICAL, "不安全反序列化"),
        "pickle.loads": (VulnerabilitySeverity.CRITICAL, "不安全反序列化"),
        "yaml.load": (VulnerabilitySeverity.CRITICAL, "不安全YAML解析"),
        "yaml.unsafe_load": (VulnerabilitySeverity.CRITICAL, "不安全YAML解析"),
        "marshal.load": (VulnerabilitySeverity.HIGH, " marshal反序列化"),
        "eval": (VulnerabilitySeverity.CRITICAL, "动态执行"),
        
        # 网络
        "urllib.urlopen": (VulnerabilitySeverity.LOW, "URL打开"),
        "urllib.request.urlopen": (VulnerabilitySeverity.LOW, "URL打开"),
        "requests.get": (VulnerabilitySeverity.LOW, "HTTP请求"),
        "requests.post": (VulnerabilitySeverity.LOW, "HTTP请求"),
        "socket.connect": (VulnerabilitySeverity.LOW, "socket连接"),
    }
    
    # 危险模块
    DANGEROUS_MODULES = {
        "pickle": VulnerabilitySeverity.HIGH,
        "yaml": VulnerabilitySeverity.HIGH,
        "marshal": VulnerabilitySeverity.HIGH,
        "pty": VulnerabilitySeverity.CRITICAL,
        "tty": VulnerabilitySeverity.HIGH,
        "termios": VulnerabilitySeverity.HIGH,
        "signal": VulnerabilitySeverity.LOW,
        "ctypes": VulnerabilitySeverity.HIGH,
    }
    
    # SQL注入关键字
    SQL_KEYWORDS = [
        "SELECT", "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "EXEC",
        "UNION", "EXECUTE", "TRUNCATE"
    ]
    
    # 危险正则模式
    PATTERNS = {
        "command_injection": [
            r"os\.system\s*\(",
            r"subprocess\.(call|run|Popen|getoutput|check_output)\s*\(",
            r"commands\.(getoutput|getstatusoutput)\s*\(",
            r"\.execute\s*\(\s*['\"].*?\%.*?['\"]",
            r"\.execute\s*\(\s*['\"].*?format\s*\(",
            r"\.format\s*\(\s*.*?(?:request|input|user|param)",
        ],
        "sql_injection": [
            r"(?:execute|executemany|cursor)\s*\(\s*['\"].*?\%",
            r"(?:execute|executemany)\s*\(\s*f['\"]",
            r"(?:execute|executemany)\s*\(\s*['\"].*?\.format\s*\(",
            r"(?:execute|executemany)\s*\(\s*['\"].*?\+",
        ],
        "path_traversal": [
            r"open\s*\([^)]*\+",
            r"open\s*\([^)]*\%",
            r"open\s*\([^)]*\.format\s*\(",
            r"os\.path\.join\s*\([^)]*\+",
            r"Path\s*\([^)]*\+",
        ],
        "hardcoded_secret": [
            r"password\s*=\s*['\"][^'\"]+['\"]",
            r"api_key\s*=\s*['\"][^'\"]+['\"]",
            r"secret\s*=\s*['\"][^'\"]+['\"]",
            r"token\s*=\s*['\"][a-zA-Z0-9_\-]{20,}['\"]",
            r"Authorization\s*:\s*Bearer\s+[a-zA-Z0-9_\-\.]+",
            r"private_key\s*=\s*['\"]",
            r"aws_access_key\s*=\s*['\"]",
        ],
    }


class ASTAnalyzer(ast.NodeVisitor):
    """AST分析器"""
    
    def __init__(self):
        self.findings: List[VulnerabilityFinding] = []
        self.source_lines: List[str] = []
        
    def analyze(self, tree: ast.AST, source_lines: List[str]) -> List[VulnerabilityFinding]:
        """分析AST"""
        self.source_lines = source_lines
        self.findings = []
        self.visit(tree)
        return self.findings
    
    def _get_line_content(self, lineno: int) -> str:
        """获取行内容"""
        if 0 < lineno <= len(self.source_lines):
            return self.source_lines[lineno - 1].strip()
        return ""
    
    def visit_Call(self, node: ast.Call) -> None:
        """访问函数调用节点"""
        # 检查危险函数调用
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"
        
        if func_name in DangerousFunction.FUNCTIONS:
            severity, description = DangerousFunction.FUNCTIONS[func_name]
            self.findings.append(VulnerabilityFinding(
                vuln_type=VulnerabilityType.DANGEROUS_FUNCTION,
                severity=severity,
                line_number=node.lineno or 0,
                column=node.col_offset or 0,
                code_snippet=self._get_line_content(node.lineno or 0),
                description=f"危险函数调用: {func_name} - {description}",
                recommendation=f"避免使用 {func_name}，考虑使用更安全的替代方案"
            ))
        
        # 检查 __import__
        if func_name == "__import__" and node.args:
            if isinstance(node.args[0], ast.Constant):
                module_name = node.args[0].value
                if module_name in DangerousFunction.DANGEROUS_MODULES:
                    severity = DangerousFunction.DANGEROUS_MODULES[module_name]
                    self.findings.append(VulnerabilityFinding(
                        vuln_type=VulnerabilityType.UNSAFE_IMPORT,
                        severity=severity,
                        line_number=node.lineno or 0,
                        column=node.col_offset or 0,
                        code_snippet=self._get_line_content(node.lineno or 0),
                        description=f"危险模块导入: {module_name}",
                        recommendation=f"避免动态导入危险模块"
                    ))
        
 self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> None:
        """访问导入节点"""
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name in DangerousFunction.DANGEROUS_MODULES:
                severity = DangerousFunction.DANGEROUS_MODULES[module_name]
                self.findings.append(VulnerabilityFinding(
                    vuln_type=VulnerabilityType.UNSAFE_IMPORT,
                    severity=severity,
                    line_number=node.lineno or 0,
                    column=node.col_offset or 0,
                    code_snippet=self._get_line_content(node.lineno or 0),
                    description=f"危险模块导入: {module_name}",
                    recommendation=f"考虑使用更安全的替代方案"
                ))
    
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """访问from导入节点"""
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name in DangerousFunction.DANGEROUS_MODULES:
                severity = DangerousFunction.DANGEROUS_MODULES[module_name]
                self.findings.append(VulnerabilityFinding(
                    vuln_type=VulnerabilityType.UNSAFE_IMPORT,
                    severity=severity,
                    line_number=node.lineno or 0,
                    column=node.col_offset or 0,
                    code_snippet=self._get_line_content(node.lineno or 0),
                    description=f"危险模块导入: {module_name}",
                    recommendation=f"考虑使用更安全的替代方案"
                ))
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """访问赋值节点 - 检查硬编码密钥"""
        # 检查硬编码密钥
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id.lower()
                if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                    value = node.value.value
                    if any(kw in var_name for kw in ['password', 'secret', 'key', 'token', 'api']):
                        if len(value) > 5 and not value.startswith('${'):
                            self.findings.append(VulnerabilityFinding(
                                vuln_type=VulnerabilityType.HARDCODED_SECRET,
                                severity=VulnerabilitySeverity.HIGH,
                                line_number=node.lineno or 0,
                                column=node.col_offset or 0,
                                code_snippet=self._get_line_content(node.lineno or 0),
                                description=f"可能存在硬编码密钥: {var_name}",
                                recommendation="使用环境变量或密钥管理系统存储敏感信息"
                            ))
        self.generic_visit(node)


class SecurityChecker:
    """基于规则的安全检查器"""
    
    def __init__(self):
        self.findings: List[VulnerabilityFinding] = []
        
    def check(self, source_code: str, file_path: str = "") -> List[VulnerabilityFinding]:
        """检查源代码"""
        self.findings = []
        lines = source_code.split('\n')
        
        # 检查各种模式
        for pattern_type, patterns in DangerousFunction.PATTERNS.items():
            for pattern in patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        vuln_type = self._get_vuln_type(pattern_type)
                        severity = self._get_severity(pattern_type)
                        
                        self.findings.append(VulnerabilityFinding(
                            vuln_type=vuln_type,
                            severity=severity,
                            line_number=i,
                            column=0,
                            code_snippet=line.strip(),
                            description=self._get_description(pattern_type),
                            recommendation=self._get_recommendation(pattern_type)
                        ))
        
        return self.findings
    
    def _get_vuln_type(self, pattern_type: str) -> VulnerabilityType:
        """获取漏洞类型"""
        mapping = {
            "command_injection": VulnerabilityType.COMMAND_INJECTION,
            "sql_injection": VulnerabilityType.SQL_INJECTION,
            "path_traversal": VulnerabilityType.PATH_TRAVERSAL,
            "hardcoded_secret": VulnerabilityType.HARDCODED_SECRET,
        }
        return mapping.get(pattern_type, VulnerabilityType.DANGEROUS_FUNCTION)
    
    def _get_severity(self, pattern_type: str) -> VulnerabilitySeverity:
        """获取严重等级"""
        mapping = {
            "command_injection": VulnerabilitySeverity.CRITICAL,
            "sql_injection": VulnerabilitySeverity.HIGH,
            "path_traversal": VulnerabilitySeverity.MEDIUM,
            "hardcoded_secret": VulnerabilitySeverity.HIGH,
        }
        return mapping.get(pattern_type, VulnerabilitySeverity.MEDIUM)
    
    def _get_description(self, pattern_type: str) -> str:
        """获取描述"""
        mapping = {
            "command_injection": "可能存在命令注入漏洞",
            "sql_injection": "可能存在SQL注入漏洞",
            "path_traversal": "可能存在路径遍历漏洞",
            "hardcoded_secret": "发现硬编码的敏感信息",
        }
        return mapping.get(pattern_type, "发现潜在安全问题")
    
    def _get_recommendation(self, pattern_type: str) -> str:
        """获取建议"""
        mapping = {
            "command_injection": "使用subprocess.run时设置shell=False，并验证所有输入",
            "sql_injection": "使用参数化查询或ORM框架",
            "path_traversal": "验证并规范化所有文件路径，使用os.path.realpath()",
            "hardcoded_secret": "使用环境变量或密钥管理系统",
        }
        return mapping.get(pattern_type, "请审查代码确保安全")


class CodeSecurityAnalyzer:
    """代码安全分析器主类"""
    
    def __init__(self, enable_ast: bool = True, enable_pattern: bool = True):
        self.enable_ast = enable_ast
        self.enable_pattern = enable_pattern
        self.ast_analyzer = ASTAnalyzer()
        self.pattern_checker = SecurityChecker()
        self._scan_history: List[VulnerabilityReport] = []
        
    def analyze_file(self, file_path: str) -> VulnerabilityReport:
        """分析文件"""
        import time
        start_time = time.time()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception as e:
            return VulnerabilityReport(
                file_path=file_path,
                total_lines=0,
                findings=[],
                scan_time=time.time() - start_time,
                language="unknown"
            )
        
        return self.analyze(source_code, file_path)
    
    def analyze(self, source_code: str, file_path: str = "") -> VulnerabilityReport:
        """分析源代码"""
        import time
        start_time = time.time()
        
        lines = source_code.split('\n')
        findings: List[VulnerabilityFinding] = []
        
        # AST分析
        if self.enable_ast:
            try:
                tree = ast.parse(source_code)
                ast_findings = self.ast_analyzer.analyze(tree, lines)
                findings.extend(ast_findings)
            except SyntaxError:
                pass
        
        # 模式匹配分析
        if self.enable_pattern:
            pattern_findings = self.pattern_checker.check(source_code, file_path)
            findings.extend(pattern_findings)
        
        # 去重
        findings = self._deduplicate_findings(findings)
        
        # 排序
        findings.sort(key=lambda x: (x.severity.value, x.line_number))
        
        report = VulnerabilityReport(
            file_path=file_path,
            total_lines=len(lines),
            findings=findings,
            scan_time=time.time() - start_time,
            language="python"
        )
        
        self._scan_history.append(report)
        return report
    
    def analyze_directory(self, directory: str, extensions: List[str] = ['.py']) -> List[VulnerabilityReport]:
        """分析目录"""
        reports = []
        dir_path = Path(directory)
        
        for ext in extensions:
            for file_path in dir_path.rglob(f'*{ext}'):
                # 跳过虚拟环境和测试文件
                if any(skip in str(file_path) for skip in ['venv', '.venv', 'env', '__pycache__', 'test_', '_test.']):
                    continue
                try:
                    report = self.analyze_file(str(file_path))
                    reports.append(report)
                except Exception:
                    pass
        
        return reports
    
    def _deduplicate_findings(self, findings: List[VulnerabilityFinding]) -> List[VulnerabilityFinding]:
        """去重"""
        seen = set()
        unique = []
        
        for f in findings:
            key = (f.vuln_type, f.line_number, f.column)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        
        return unique
    
    def get_scan_history(self) -> List[VulnerabilityReport]:
        """获取扫描历史"""
        return self._scan_history
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self._scan_history:
            return {}
        
        total_files = len(self._scan_history)
        total_findings = sum(len(r.findings) for r in self._scan_history)
        
        severity_counts = defaultdict(int)
        type_counts = defaultdict(int)
        
        for report in self._scan_history:
            for finding in report.findings:
                severity_counts[finding.severity.value] += 1
                type_counts[finding.vuln_type.value] += 1
        
        return {
            "total_files_scanned": total_files,
            "total_findings": total_findings,
            "severity_breakdown": dict(severity_counts),
            "type_breakdown": dict(type_counts)
        }


# 全局分析器实例
_global_analyzer = CodeSecurityAnalyzer()


def analyze_code(source_code: str, file_path: str = "") -> VulnerabilityReport:
    """全局分析函数"""
    return _global_analyzer.analyze(source_code, file_path)


def analyze_file(file_path: str) -> VulnerabilityReport:
    """全局文件分析函数"""
    return _global_analyzer.analyze_file(file_path)


def analyze_directory(directory: str) -> List[VulnerabilityReport]:
    """全局目录分析函数"""
    return _global_analyzer.analyze_directory(directory)


def get_analyzer() -> CodeSecurityAnalyzer:
    """获取全局分析器"""
    return _global_analyzer
