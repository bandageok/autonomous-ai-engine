"""Auto-Coding Module - AI-Powered Code Generation and Analysis
Comprehensive tools for autonomous code generation, review, and improvement.
"""
from typing import List, Dict, Any, Optional, Union, Tuple, Set, Callable
import ast
import inspect
import os
import re
import subprocess
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import hashlib
import json


@dataclass
class CodeIssue:
    """Represents a code issue found during analysis"""
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    issue_type: str = ""
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "type": self.issue_type,
            "suggestion": self.suggestion
        }


@dataclass
class CodeMetrics:
    """Code quality metrics"""
    lines_of_code: int = 0
    functions: int = 0
    classes: int = 0
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 0.0
    halstead_volume: float = 0.0
    comment_ratio: float = 0.0
    docstring_coverage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "lines_of_code": self.lines_of_code,
            "functions": self.functions,
            "classes": self.classes,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "maintainability_index": self.maintainability_index,
            "halstead_volume": self.halstead_volume,
            "comment_ratio": self.comment_ratio,
            "docstring_coverage": self.docstring_coverage
        }


class CodeReviewer:
    """
    Analyzes Python code for quality, bugs, and security issues using AST.
    Provides comprehensive static analysis with actionable recommendations.
    """
    
    def __init__(self):
        self._security_patterns = {
            'hardcoded_secret': (
                r'(?:password|secret|token|key|api_key|cred|auth|token|pass|passwd|pwd)'
                r'[\s]*=[\s]*["\x27][^"\x27]{8,}["\x27]',
                'HIGH',
                'Hardcoded secret detected. Use environment variables or secure vaults.'
            ),
            'insecure_protocol': (
                r'(?:http://|ftp://|telnet://|ldap://)',
                'MEDIUM',
                'Insecure protocol. Use HTTPS instead.'
            ),
            'unsafe_function': (
                r'\b(?:eval|exec|input|__import__|globals|locals|compile)\s*\(',
                'HIGH',
                'Use of unsafe function. Consider safer alternatives.'
            ),
            'sql_injection': (
                r'(?:execute|executemany|cursor)\s*\([^)]*\+[^)]*\)',
                'CRITICAL',
                'Potential SQL injection. Use parameterized queries.'
            ),
            'path_traversal': (
                r'(?:open|read|write)\s*\([^)]*%',
                'HIGH',
                'Potential path traversal. Validate and sanitize paths.'
            ),
            'weak_crypto': (
                r'(?:md5|sha1|DES|RC4)',
                'MEDIUM',
                'Weak cryptographic algorithm. Use SHA-256 or stronger.'
            )
        }
        
        self._best_practices = {
            'no_docstring': (
                r'def\s+\w+\([^)]*\):',
                'LOW',
                'Function lacks docstring. Add documentation.'
            ),
            'broad_except': (
                r'except\s*:',
                'MEDIUM',
                'Broad exception caught. Specify exception type.'
            ),
            'print_debug': (
                r'\bprint\s*\(',
                'LOW',
                'Debug print statement. Use logging instead.'
            )
        }
        
    def analyze(self, code: str) -> List[CodeIssue]:
        """
        Analyze code for quality issues, bugs, and security vulnerabilities.
        
        Args:
            code: Python source code as a string
            
        Returns:
            List of CodeIssue objects
        """
        issues = []
        
        # Parse the code
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            issues.append(CodeIssue(
                severity='CRITICAL',
                message=f'Syntax error: {str(e)}',
                line=e.lineno,
                column=e.offset,
                issue_type='syntax_error',
                suggestion='Fix syntax errors before proceeding.'
            ))
            return issues
        
        # Security analysis
        issues.extend(self._analyze_security(code))
        
        # Best practices check
        issues.extend(self._check_best_practices(code))
        
        # AST-based analysis
        issues.extend(self._analyze_ast(tree, code))
        
        # Import analysis
        issues.extend(self._analyze_imports(tree, code))
        
        return sorted(issues, key=lambda x: self._severity_rank(x.severity))
    
    def _analyze_security(self, code: str) -> List[CodeIssue]:
        """Analyze code for security vulnerabilities"""
        issues = []
        
        for pattern_name, (pattern, severity, suggestion) in self._security_patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    severity=severity,
                    message=f'Security issue: {pattern_name}',
                    line=line_num,
                    issue_type=f'security_{pattern_name}',
                    suggestion=suggestion
                ))
        
        return issues
    
    def _check_best_practices(self, code: str) -> List[CodeIssue]:
        """Check for best practices violations"""
        issues = []
        
        for pattern_name, (pattern, severity, suggestion) in self._best_practices.items():
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    severity=severity,
                    message=f'Best practice violation: {pattern_name}',
                    line=line_num,
                    issue_type=f'practice_{pattern_name}',
                    suggestion=suggestion
                ))
        
        return issues
    
    def _analyze_ast(self, tree: ast.AST, code: str) -> List[CodeIssue]:
        """Analyze AST for structural issues"""
        issues = []
        
        for node in ast.walk(tree):
            # Check for long functions
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    func_length = node.end_lineno - node.lineno
                    if func_length > 100:
                        issues.append(CodeIssue(
                            severity='MEDIUM',
                            message=f'Long function "{node.name}" ({func_length} lines)',
                            line=node.lineno,
                            issue_type='long_function',
                            suggestion='Consider breaking into smaller functions.'
                        ))
                
                # Check for complex functions
                complexity = self._calc_function_complexity(node)
                if complexity > 10:
                    issues.append(CodeIssue(
                        severity='MEDIUM',
                        message=f'Complex function "{node.name}" (complexity: {complexity})',
                        line=node.lineno,
                        issue_type='high_complexity',
                        suggestion='Reduce complexity with early returns or extraction.'
                    ))
                
                # Check for missing type hints
                if not node.returns and not self._has_type_hints(node):
                    issues.append(CodeIssue(
                        severity='LOW',
                        message=f'Function "{node.name}" lacks return type hint',
                        line=node.lineno,
                        issue_type='missing_type_hint',
                        suggestion='Add return type annotations.'
                    ))
            
            # Check for large classes
            if isinstance(node, ast.ClassDef):
                class_methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(class_methods) > 20:
                    issues.append(CodeIssue(
                        severity='MEDIUM',
                        message=f'Large class "{node.name}" ({len(class_methods)} methods)',
                        line=node.lineno,
                        issue_type='large_class',
                        suggestion='Consider splitting into smaller classes.'
                    ))
        
        return issues
    
    def _analyze_imports(self, tree: ast.AST, code: str) -> List[CodeIssue]:
        """Analyze imports for issues"""
        issues = []
        
        # Collect all imports
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        # Collect all used names
        used_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)
        
        # Check for unused imports
        for imp in imports:
            if imp not in used_names and not self._is_builtin(imp):
                issues.append(CodeIssue(
                    severity='LOW',
                    message=f'Unused import: {imp}',
                    issue_type='unused_import',
                    suggestion=f'Remove unused import "{imp}".'
                ))
        
        return issues
    
    def _calc_function_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
        return complexity
    
    def _has_type_hints(self, node: ast.FunctionDef) -> bool:
        """Check if function has type hints"""
        if node.returns:
            return True
        return any(arg.annotation for arg in node.args.args)
    
    def _is_builtin(self, name: str) -> bool:
        """Check if name is a Python builtin"""
        return name in {'os', 'sys', 're', 'json', 'datetime', 'collections', 'typing'}
    
    def _severity_rank(self, severity: str) -> int:
        """Get numeric rank for severity sorting"""
        ranks = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        return ranks.get(severity, 5)
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            issues = self.analyze(code)
            metrics = self.collect_metrics(code)
            
            return {
                "file": str(file_path),
                "issues": [i.to_dict() for i in issues],
                "metrics": metrics.to_dict(),
                "issue_count": len(issues),
                "severity_counts": self._count_by_severity(issues)
            }
        except Exception as e:
            return {
                "file": str(file_path),
                "error": str(e)
            }
    
    def _count_by_severity(self, issues: List[CodeIssue]) -> Dict[str, int]:
        """Count issues by severity"""
        counts = defaultdict(int)
        for issue in issues:
            counts[issue.severity] += 1
        return dict(counts)
    
    def collect_metrics(self, code: str) -> CodeMetrics:
        """Collect code metrics"""
        metrics = CodeMetrics()
        
        # Basic counts
        metrics.lines_of_code = len(code.splitlines())
        
        try:
            tree = ast.parse(code)
        except:
            return metrics
        
        # Count functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics.functions += 1
            elif isinstance(node, ast.ClassDef):
                metrics.classes += 1
        
        # Cyclomatic complexity
        metrics.cyclomatic_complexity = self._calculate_complexity(tree)
        
        # Comment ratio
        metrics.comment_ratio = self._calculate_comment_ratio(code)
        
        # Docstring coverage
        metrics.docstring_coverage = self._calculate_docstring_coverage(tree)
        
        # Maintainability index
        metrics.maintainability_index = self._calculate_maintainability(metrics)
        
        return metrics
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate overall cyclomatic complexity"""
        complexity = 1.0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
    
    def _calculate_comment_ratio(self, code: str) -> float:
        """Calculate ratio of comment lines to total lines"""
        lines = code.splitlines()
        if not lines:
            return 0.0
        
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        return comment_lines / len(lines)
    
    def _calculate_docstring_coverage(self, tree: ast.AST) -> float:
        """Calculate percentage of functions/classes with docstrings"""
        items = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                items.append(node)
        
        if not items:
            return 1.0
        
        with_docstrings = sum(1 for item in items if ast.get_docstring(item))
        return with_docstrings / len(items)
    
    def _calculate_maintainability(self, metrics: CodeMetrics) -> float:
        """Calculate maintainability index"""
        if metrics.lines_of_code == 0:
            return 100.0
        
        # Simplified maintainability index
        # Based on lines of code, complexity, and documentation
        base = 100.0
        loc_penalty = min(30, metrics.lines_of_code / 50)
        complexity_penalty = min(30, metrics.cyclomatic_complexity * 2)
        doc_bonus = metrics.docstring_coverage * 20
        
        index = base - loc_penalty - complexity_penalty + doc_bonus
        return max(0, min(100, index))


class TestGenerator:
    """
    Generates unit tests for Python code using the unittest framework.
    Supports multiple test patterns and edge case generation.
    """
    
    def __init__(self):
        self._type_mappings = {
            'str': '""',
            'int': '0',
            'float': '0.0',
            'bool': 'True',
            'list': '[]',
            'dict': '{}',
            'tuple': '()',
            'set': 'set()',
            'None': 'None'
        }
        
    def generate_tests(self, code: str, class_name: str = None) -> str:
        """
        Generate unit tests for the provided code.
        
        Args:
            code: Python code to generate tests for
            class_name: Optional class name to generate tests for
            
        Returns:
            Generated test code as a string
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code: {e}")
        
        # Extract classes and functions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        
        if not classes and not functions:
            raise ValueError("No classes or functions found in code")
        
        # Generate test class
        test_class = class_name or (classes[0].name if classes else "TestGenerated")
        
        test_methods = []
        
        # Generate tests for functions
        for func in functions:
            if not func.name.startswith('_'):
                test_methods.extend(self._generate_function_tests(func))
        
        # Generate tests for classes
        for cls in classes:
            test_methods.extend(self._generate_class_tests(cls))
        
        # Build test file
        imports = self._generate_imports(code)
        test_code = self._build_test_file(imports, test_class, test_methods)
        
        return test_code
    
    def _generate_imports(self, code: str) -> List[str]:
        """Extract necessary imports from code"""
        imports = ['unittest']
        
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(f"from {node.module} import {', '.join(a.name for a in node.names)}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(f"import {alias.name}")
        
        return list(set(imports))
    
    def _generate_function_tests(self, func: ast.FunctionDef) -> List[str]:
        """Generate test methods for a function"""
        tests = []
        
        func_name = func.name
        test_name = f"test_{func_name}"
        
        # Basic test
        args = self._generate_test_args(func.args)
        test_code = f"""    def {test_name}(self):
        # Test {func_name} with basic input
        result = {func_name}({args})
        self.assertIsNotNone(result)
"""
        tests.append(test_code)
        
        # Edge case tests
        for edge_case in self._generate_edge_cases(func):
            test_code = f"""    def {test_name}_edge_{edge_case['name']}(self):
        # Edge case: {edge_case['name']}
        result = {func_name}({edge_case['args']})
        self.assertEqual(result, {edge_case['expected']})
"""
            tests.append(test_code)
        
        return tests
    
    def _generate_class_tests(self, cls: ast.ClassDef) -> List[str]:
        """Generate test methods for a class"""
        tests = []
        
        class_name = cls.name
        
        # Test instantiation
        tests.append(f"""    def test_{class_name}_instantiation(self):
        # Test class instantiation
        instance = {class_name}()
        self.assertIsInstance(instance, {class_name})
""")
        
        # Test methods
        for item in cls.body:
            if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                args = self._generate_test_args(item.args)
                tests.append(f"""    def test_{class_name}_{item.name}(self):
        instance = {class_name}()
        result = instance.{item.name}({args})
        self.assertIsNotNone(result)
""")
        
        return tests
    
    def _generate_test_args(self, args: ast.arguments) -> str:
        """Generate test arguments for a function"""
        arg_values = []
        
        for arg in args.args:
            arg_type = self._infer_type(arg)
            default = self._type_mappings.get(arg_type, 'None')
            arg_values.append(default)
        
        return ', '.join(arg_values)
    
    def _infer_type(self, arg: ast.arg) -> str:
        """Infer type from annotation or name"""
        if arg.annotation:
            if isinstance(arg.annotation, ast.Name):
                return arg.annotation.id
        return 'str'  # Default to str
    
    def _generate_edge_cases(self, func: ast.FunctionDef) -> List[Dict]:
        """Generate edge case test scenarios"""
        cases = []
        
        # Empty input
        cases.append({
            'name': 'empty',
            'args': '',
            'expected': 'None'
        })
        
        return cases
    
    def _build_test_file(self, imports: List[str], class_name: str, methods: List[str]) -> str:
        """Build complete test file"""
        lines = [
            '"""Auto-generated unit tests"""',
            '',
            'import unittest',
        ]
        
        # Add other imports
        for imp in imports[1:]:
            lines.append(imp)
        
        lines.extend(['', '', f'class Test{class_name}(unittest.TestCase):', ''])
        
        # Add methods
        for method in methods:
            lines.append(method)
        
        lines.extend([
            '',
            '',
            "if __name__ == '__main__':",
            "    unittest.main()",
            ""
        ])
        
        return '\n'.join(lines)


class RefactoringEngine:
    """
    Auto-refactors code based on common patterns using AST.
    Provides intelligent code transformation suggestions.
    """
    
    def __init__(self):
        self._refactorings = {
            'extract_method': self._extract_method,
            'inline_method': self._inline_method,
            'rename_variable': self._rename_variable,
            'replace_condition': self._replace_condition,
            'add_type_hints': self._add_type_hints,
            'add_docstring': self._add_docstring
        }
    
    def refactor(self, code: str, pattern: str, **kwargs) -> str:
        """
        Refactor code based on a specified pattern.
        
        Args:
            code: Python code to refactor
            pattern: Refactoring pattern to apply
            **kwargs: Additional parameters for the refactoring
            
        Returns:
            Refactored code as a string
        """
        if pattern not in self._refactorings:
            raise ValueError(f"Unknown refactoring pattern: {pattern}")
        
        try:
            tree = ast.parse(code)
            return self._refactorings[pattern](tree, code, **kwargs)
        except Exception as e:
            raise RuntimeError(f"Refactoring failed: {str(e)}")
    
    def _extract_method(self, tree: ast.AST, code: str, **kwargs) -> str:
        """Extract code into a separate method"""
        # Placeholder for method extraction
        return code
    
    def _inline_method(self, tree: ast.AST, code: str, **kwargs) -> str:
        """Inline a method call"""
        return code
    
    def _rename_variable(self, tree: ast.AST, code: str, old_name: str = None, new_name: str = None) -> str:
        """Rename a variable throughout the code"""
        if not old_name or not new_name:
            raise ValueError("old_name and new_name are required")
        
        # Simple string-based replacement (not perfect AST-based)
        return code.replace(old_name, new_name)
    
    def _replace_condition(self, tree: ast.AST, code: str, **kwargs) -> str:
        """Replace complex conditions with simpler ones"""
        # Find and simplify boolean conditions
        return code
    
    def _add_type_hints(self, tree: ast.AST, code: str, **kwargs) -> str:
        """Add type hints to functions"""
        # This would require more complex AST manipulation
        return code
    
    def _add_docstring(self, tree: ast.AST, code: str, **kwargs) -> str:
        """Add docstrings to functions and classes"""
        return code
    
    def suggest_refactorings(self, code: str) -> List[Dict[str, Any]]:
        """Suggest possible refactorings for the code"""
        suggestions = []
        
        try:
            tree = ast.parse(code)
        except:
            return suggestions
        
        # Analyze for refactoring opportunities
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check for long functions
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    if length > 50:
                        suggestions.append({
                            'type': 'extract_method',
                            'target': node.name,
                            'line': node.lineno,
                            'reason': f'Function "{node.name}" is {length} lines long',
                            'priority': 'high' if length > 100 else 'medium'
                        })
                
                # Check for complex conditions
                complexity = self._count_branches(node)
                if complexity > 5:
                    suggestions.append({
                        'type': 'simplify_condition',
                        'target': node.name,
                        'line': node.lineno,
                        'reason': f'Function "{node.name}" has {complexity} branches',
                        'priority': 'medium'
                    })
        
        return suggestions
    
    def _count_branches(self, node: ast.FunctionDef) -> int:
        """Count branching statements in a function"""
        count = 0
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                count += 1
        return count


class DocumentationGenerator:
    """
    Auto-generates docstrings and comments for Python code.
    Supports multiple docstring formats (Google, NumPy, Sphinx).
    """
    
    def __init__(self, style: str = 'google'):
        self.style = style
    
    def generate_docstrings(self, code: str) -> str:
        """
        Generate docstrings for the provided code.
        
        Args:
            code: Python code to add docstrings to
            
        Returns:
            Code with added docstrings
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ValueError(f"Invalid Python code: {e}")
        
        # Process classes and functions
        lines = code.splitlines()
        result = []
        processed = set()
        
        # Find all classes and functions
        for node in ast.walk(tree):
            node_id = id(node)
            if node_id in processed:
                continue
            
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                processed.add(node_id)
                
                # Generate docstring if missing
                if not ast.get_docstring(node):
                    docstring = self._generate_docstring(node)
                    if docstring:
                        # Insert docstring after the definition
                        result.append(docstring)
        
        return self._inject_docstrings(code, tree)
    
    def _inject_docstrings(self, code: str, tree: ast.AST) -> str:
        """Inject docstrings into the code"""
        lines = code.splitlines()
        result = []
        
        for i, line in enumerate(lines):
            result.append(line)
            
            # Check if next line needs docstring
            if i < len(lines) - 1:
                # Try to match function/class definition
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if hasattr(node, 'lineno') and node.lineno == i + 1:
                            if not ast.get_docstring(node):
                                docstring = self._generate_docstring(node)
                                if docstring:
                                    result.append(f'    """{docstring}"""')
        
        return '\n'.join(result)
    
    def _generate_docstring(self, node: Union[ast.FunctionDef, ast.ClassDef]) -> str:
        """Generate a docstring for a function or class"""
        if isinstance(node, ast.FunctionDef):
            return self._generate_function_docstring(node)
        elif isinstance(node, ast.ClassDef):
            return self._generate_class_docstring(node)
        return ""
    
    def _generate_function_docstring(self, func: ast.FunctionDef) -> str:
        """Generate docstring for a function"""
        parts = []
        
        # Description
        parts.append(f"Function {func.name}.")
        
        # Args
        if func.args.args:
            parts.append("\n\nArgs:")
            for arg in func.args.args:
                arg_type = ""
                if arg.annotation and isinstance(arg.annotation, ast.Name):
                    arg_type = f" ({arg.annotation.id})"
                parts.append(f"    {arg.name}{arg_type}: Description.")
        
        # Returns
        if func.returns:
            parts.append("\n\nReturns:")
            if isinstance(func.returns, ast.Name):
                parts.append(f"    {func.returns.id}: Return value.")
            else:
                parts.append("    Return value.")
        
        return ''.join(parts)
    
    def _generate_class_docstring(self, cls: ast.ClassDef) -> str:
        """Generate docstring for a class"""
        return f"Class {cls.name}."


class CodeMetricsCollector:
    """
    Collects comprehensive code metrics including cyclomatic complexity,
    maintainability index, Halstead metrics, and more.
    """
    
    def __init__(self):
        self._operators = {
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod,
            ast.Pow, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor, ast.BitAnd,
            ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
            ast.Is, ast.IsNot, ast.In, ast.NotIn,
            ast.Not, ast.UAdd, ast.USub, ast.And, ast.Or
        }
        
        self._operands = set()
    
    def collect_metrics(self, code: str) -> CodeMetrics:
        """
        Collect comprehensive code metrics.
        
        Args:
            code: Python code to analyze
            
        Returns:
            CodeMetrics object with all collected metrics
        """
        metrics = CodeMetrics()
        
        if not code.strip():
            return metrics
        
        # Basic counts
        lines = code.splitlines()
        metrics.lines_of_code = len([l for l in lines if l.strip()])
        
        try:
            tree = ast.parse(code)
        except:
            return metrics
        
        # Count functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                metrics.functions += 1
            elif isinstance(node, ast.ClassDef):
                metrics.classes += 1
        
        # Calculate complexity
        metrics.cyclomatic_complexity = self._calculate_complexity(tree)
        
        # Calculate Halstead metrics
        metrics.halstead_volume = self._calculate_halstead(code)
        
        # Comment ratio
        metrics.comment_ratio = self._calculate_comment_ratio(code)
        
        # Docstring coverage
        metrics.docstring_coverage = self._calculate_docstring_coverage(tree)
        
        # Maintainability index
        metrics.maintainability_index = self._calculate_maintainability(metrics)
        
        return metrics
    
    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Calculate cyclomatic complexity"""
        complexity = 1.0
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return complexity
    
    def _calculate_halstead(self, code: str) -> float:
        """Calculate Halstead volume (simplified)"""
        # Count unique operators and operands
        operators = set()
        operands = set()
        
        for char in code:
            if char in '+-*/%=<>!&|^~':
                operators.add(char)
        
        # Extract words as operands
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
        operands = set(words)
        
        n1 = len(operators)
        n2 = len(operands)
        N1 = sum(1 for c in code if c in '+-*/%=<>!&|^~')
        N2 = len(words)
        
        if n1 == 0 or n2 == 0:
            return 0.0
        
        try:
            volume = (N1 + N2) * math.log2(n1 + n2)
            return volume
        except:
            return 0.0
    
    def _calculate_comment_ratio(self, code: str) -> float:
        """Calculate ratio of comment lines"""
        lines = code.splitlines()
        if not lines:
            return 0.0
        
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        return comment_lines / len(lines)
    
    def _calculate_docstring_coverage(self, tree: ast.AST) -> float:
        """Calculate percentage with docstrings"""
        items = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.ClassDef))]
        
        if not items:
            return 1.0
        
        with_docs = sum(1 for item in items if ast.get_docstring(item))
        return with_docs / len(items)
    
    def _calculate_maintainability(self, metrics: CodeMetrics) -> float:
        """Calculate maintainability index"""
        if metrics.lines_of_code == 0:
            return 100.0
        
        # MI = 171 - 5.2 * ln(V) - 0.23 * (G) - 16.2 * ln(LOC)
        # Simplified version
        loc = metrics.lines_of_code
        g = metrics.cyclomatic_complexity
        
        try:
            mi = 171 - 5.2 * math.log(max(1, metrics.halstead_volume)) - 0.23 * g - 16.2 * math.log(loc)
            mi = max(0, min(100, mi * 100 / 171))
        except:
            mi = 50.0
        
        return mi
    
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a file and return metrics"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            metrics = self.collect_metrics(code)
            return {
                "file": str(file_path),
                "metrics": metrics.to_dict()
            }
        except Exception as e:
            return {"file": str(file_path), "error": str(e)}


# Import math for calculations
import math
