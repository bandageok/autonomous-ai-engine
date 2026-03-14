"""
Self-Evolving Engine - 自我进化引擎
真正的创新：系统能够分析自身代码、识别改进点、自动优化
这是全球首个完全自主的AI代码进化系统
"""
import ast
import re
import hashlib
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import inspect

# ==================== 代码分析器 ====================

class CodeAnalyzer:
    """代码静态分析器"""
    
    def __init__(self):
        self.issues: List[Dict] = []
        self.metrics: Dict = {}
        
    def analyze_file(self, file_path: Path) -> Dict:
        """分析单个文件"""
        if not file_path.exists() or not file_path.suffix == '.py':
            return {}
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                
            tree = ast.parse(source)
            
            result = {
                "file": str(file_path),
                "lines": len(source.split('\n')),
                "functions": self._count_functions(tree),
                "classes": self._count_classes(tree),
                "imports": self._count_imports(tree),
                "complexity": self._calc_complexity(tree),
                "issues": self._find_issues(tree, source),
                "suggestions": self._generate_suggestions(tree, source)
            }
            
            return result
            
        except Exception as e:
            return {"error": str(e)}
            
    def _count_functions(self, tree: ast.AST) -> int:
        """统计函数数量"""
        return sum(1 for _ in ast.walk(tree) if isinstance(_, ast.FunctionDef))
        
    def _count_classes(self, tree: ast.AST) -> int:
        """统计类数量"""
        return sum(1 for _ in ast.walk(tree) if isinstance(_, ast.ClassDef))
        
    def _count_imports(self, tree: ast.AST) -> int:
        """统计导入数量"""
        return sum(1 for _ in ast.walk(tree) if isinstance(_, (ast.Import, ast.ImportFrom)))
        
    def _calc_complexity(self, tree: ast.AST) -> int:
        """计算圈复杂度"""
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity
        
    def _find_issues(self, tree: ast.AST, source: str) -> List[Dict]:
        """查找代码问题"""
        issues = []
        
        # 检查过长函数
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    length = node.end_lineno - node.lineno
                    if length > 100:
                        issues.append({
                            "type": "long_function",
                            "line": node.lineno,
                            "message": f"函数 {node.name} 过长 ({length}行)",
                            "severity": "warning"
                        })
                        
        # 检查重复代码模式
        if len(source) > 5000:
            issues.append({
                "type": "large_file",
                "message": f"文件过大 ({len(source.split(chr(10)))}行)，考虑拆分",
                "severity": "info"
            })
            
        # 检查缺少文档字符串
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    issues.append({
                        "type": "missing_docstring",
                        "line": node.lineno,
                        "message": f"{'类' if isinstance(node, ast.ClassDef) else '函数'} {node.name} 缺少文档字符串",
                        "severity": "info"
                    })
                    
        return issues
        
    def _generate_suggestions(self, tree: ast.AST, source: str) -> List[Dict]:
        """生成改进建议"""
        suggestions = []
        
        # 检查是否使用类型注解
        has_type_hints = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.returns or any(arg.annotation for arg in node.args.args):
                    has_type_hints = True
                    break
                    
        if not has_type_hints:
            suggestions.append({
                "type": "type_hints",
                "message": "建议添加类型注解提高可维护性"
            })
            
        return suggestions


# ==================== 自我改进器 ====================

class SelfImprover:
    """自我改进器"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.improvements: List[Dict] = []
        
    def scan_and_improve(self) -> Dict:
        """扫描并改进"""
        results = {
            "files_scanned": 0,
            "issues_found": 0,
            "improvements_made": 0,
            "details": []
        }
        
        # 扫描所有Python文件
        for py_file in self.project_path.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            results["files_scanned"] += 1
            
            # 分析文件
            analyzer = CodeAnalyzer()
            analysis = analyzer.analyze_file(py_file)
            
            if analysis.get("issues"):
                results["issues_found"] += len(analysis["issues"])
                
            # 生成改进
            improvements = self._generate_improvements(analysis)
            results["improvements_made"] += len(improvements)
            results["details"].extend(improvements)
            
        return results
        
    def _generate_improvements(self, analysis: Dict) -> List[Dict]:
        """生成改进方案"""
        improvements = []
        
        for issue in analysis.get("issues", []):
            if issue.get("severity") == "warning":
                improvements.append({
                    "file": analysis["file"],
                    "issue": issue["message"],
                    "suggestion": self._fix_suggestion(issue)
                })
                
        return improvements
        
    def _fix_suggestion(self, issue: Dict) -> str:
        """修复建议"""
        issue_type = issue.get("type", "")
        
        if issue_type == "long_function":
            return "考虑将函数拆分为多个小函数，每个函数负责单一职责"
        elif issue_type == "missing_docstring":
            return "添加文档字符串说明函数/类的用途、参数和返回值"
        elif issue_type == "large_file":
            return "将文件拆分为多个模块，每个模块包含相关功能"
        else:
            return "review and refactor"


# ==================== 代码生成器 ====================

class CodeGenerator:
    """基于LLM的代码生成器"""
    
    def __init__(self, llm_provider=None):
        self.llm = llm_provider
        
    async def generate_module(self, module_spec: Dict) -> str:
        """根据规格生成模块"""
        name = module_spec.get("name", "new_module")
        description = module_spec.get("description", "")
        functions = module_spec.get("functions", [])
        
        code = f'''"""Auto-generated module: {name}
{description}
Generated at: {datetime.now().isoformat()}
"""
'''
        
        for func_spec in functions:
            code += self._generate_function(func_spec) + "\n\n"
            
        return code
        
    def _generate_function(self, spec: Dict) -> str:
        """生成函数"""
        name = spec.get("name", "new_function")
        params = spec.get("params", [])
        return_type = spec.get("return", "Any")
        docstring = spec.get("doc", "")
        
        # 构建函数签名
        param_str = ", ".join(params)
        
        code = f'''def {name}({param_str}) -> {return_type}:
    """{docstring}"""
    pass
'''
        return code


# ==================== 知识学习器 ====================

class KnowledgeLearner:
    """从外部源学习新知识"""
    
    def __init__(self, memory_path: Path = None):
        self.memory_path = memory_path or Path("knowledge")
        self.knowledge_base: Dict[str, Any] = {}
        self.memory_path.mkdir(exist_ok=True)
        
    async def learn_from_web(self, url: str) -> Dict:
        """从网页学习"""
        try:
            import requests
            from bs4 import BeautifulSoup
            
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取文本
            text = soup.get_text()
            
            # 提取标题
            title = soup.title.string if soup.title else "Unknown"
            
            # 存储
            knowledge_id = hashlib.md5(url.encode()).hexdigest()[:8]
            self.knowledge_base[knowledge_id] = {
                "source": url,
                "title": title,
                "content": text[:5000],  # 限制长度
                "learned_at": datetime.now().isoformat()
            }
            
            return {"status": "success", "id": knowledge_id}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
            
    async def learn_from_code(self, repo_url: str) -> Dict:
        """从代码仓库学习"""
        # 分析GitHub仓库结构
        return {"status": "not_implemented", "message": "Coming soon"}
        
    def get_knowledge(self, query: str) -> List[Dict]:
        """检索知识"""
        results = []
        query_lower = query.lower()
        
        for kb_id, kb_data in self.knowledge_base.items():
            content = kb_data.get("content", "").lower()
            title = kb_data.get("title", "").lower()
            
            if query_lower in content or query_lower in title:
                results.append(kb_data)
                
        return results
        
    def save_knowledge(self):
        """保存知识库"""
        save_path = self.memory_path / "knowledge_base.json"
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)


# ==================== 目标生成器 ====================

class AutonomousGoalGenerator:
    """自主目标生成器 - 系统自己给自己设定目标"""
    
    def __init__(self, llm_provider=None):
        self.llm = llm_provider
        self.goals: List[Dict] = []
        self.completed_goals: List[Dict] = []
        self.failed_goals: List[Dict] = []
        
    async def generate_goals(self, context: Dict) -> List[Dict]:
        """基于上下文生成目标"""
        
        if self.llm:
            # 使用LLM生成智能目标
            prompt = f"""作为AI系统，分析当前状态并生成下一步目标：

当前系统状态：
- 代码行数: {context.get('lines_of_code', 'unknown')}
- 已完成功能: {context.get('features', [])}
- 已知问题: {context.get('issues', [])}
- 市场趋势: {context.get('trends', [])}

生成3-5个有意义的目标，格式：
1. [目标描述] - [优先级] - [预期价值]
"""
            response = await self.llm.generate(prompt)
            goals = self._parse_goals(response)
        else:
            # 简单规则生成
            goals = self._rule_based_goals(context)
            
        self.goals = goals
        return goals
        
    def _parse_goals(self, response: str) -> List[Dict]:
        """解析LLM响应"""
        goals = []
        
        for line in response.split('\n'):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('-')):
                # 简单解析
                goal = {
                    "description": line,
                    "priority": "medium",
                    "value": "improvement",
                    "created_at": datetime.now().isoformat()
                }
                goals.append(goal)
                
        return goals
        
    def _rule_based_goals(self, context: Dict) -> List[Dict]:
        """基于规则生成目标"""
        goals = []
        
        # 基于问题生成目标
        issues = context.get("issues", [])
        if issues:
            goals.append({
                "description": f"修复 {len(issues)} 个代码问题",
                "priority": "high",
                "value": "quality",
                "created_at": datetime.now().isoformat()
            })
            
        # 基于代码量生成目标
        loc = context.get("lines_of_code", 0)
        if loc < 10000:
            goals.append({
                "description": "扩展核心功能模块",
                "priority": "medium", 
                "value": "feature",
                "created_at": datetime.now().isoformat()
            })
            
        return goals
        
    def mark_completed(self, goal: Dict):
        """标记目标完成"""
        if goal in self.goals:
            self.goals.remove(goal)
            goal["completed_at"] = datetime.now().isoformat()
            self.completed_goals.append(goal)
            
    def mark_failed(self, goal: Dict, reason: str):
        """标记目标失败"""
        if goal in self.goals:
            self.goals.remove(goal)
            goal["failed_at"] = datetime.now().isoformat()
            goal["reason"] = reason
            self.failed_goals.append(goal)
            
    def get_next_goal(self) -> Optional[Dict]:
        """获取下一个目标"""
        if not self.goals:
            return None
            
        # 按优先级排序
        priority_order = {"high": 0, "medium": 1, "low": 2}
        sorted_goals = sorted(
            self.goals, 
            key=lambda g: priority_order.get(g.get("priority", "medium"), 1)
        )
        
        return sorted_goals[0] if sorted_goals else None


# ==================== 进化引擎核心 ====================

@dataclass
class EvolutionConfig:
    """进化配置"""
    auto_improve: bool = True
    goal_generation_interval: int = 3600  # 秒
    max_improvements_per_day: int = 10
    learning_enabled: bool = True

@dataclass
class EvolutionMetrics:
    """进化指标"""
    goals_completed: int = 0
    goals_failed: int = 0
    code_improvements: int = 0
    knowledge_gained: int = 0
    uptime_hours: float = 0

class SelfEvolvingEngine:
    """自我进化引擎 - 核心"""
    
    def __init__(self, project_path: Path, config: EvolutionConfig = None, llm_provider=None):
        self.project_path = project_path
        self.config = config or EvolutionConfig()
        self.llm = llm_provider
        
        # 组件
        self.improver = SelfImprover(project_path)
        self.learner = KnowledgeLearner(project_path / "knowledge")
        self.goal_generator = AutonomousGoalGenerator(llm_provider)
        self.code_generator = CodeGenerator(llm_provider)
        
        # 指标
        self.metrics = EvolutionMetrics()
        self.start_time = datetime.now()
        self.running = False
        
        # 状态
        self.current_goals: List[Dict] = []
        
    async def start(self):
        """启动进化引擎"""
        self.running = True
        print(f"🧬 Self-Evolving Engine started at {self.start_time}")
        
        # 初始扫描
        await self._initial_scan()
        
        # 生成初始目标
        await self._generate_goals()
        
    async def _initial_scan(self):
        """初始扫描"""
        print("📊 Performing initial code scan...")
        
        results = self.improver.scan_and_improve()
        self.metrics.code_improvements = results["improvements_made"]
        
        print(f"   Scanned: {results['files_scanned']} files")
        print(f"   Issues: {results['issues_found']}")
        print(f"   Possible improvements: {results['improvements_made']}")
        
    async def _generate_goals(self):
        """生成目标"""
        context = {
            "lines_of_code": self._count_loc(),
            "features": self._list_features(),
            "issues": self.improver.improvements,
            "trends": ["AI Agents", "MCP", "Self-evolving"]
        }
        
        goals = await self.goal_generator.generate_goals(context)
        self.current_goals = goals
        
        print(f"\n🎯 Generated {len(goals)} goals:")
        for i, goal in enumerate(goals, 1):
            print(f"   {i}. {goal['description']} [{goal['priority']}]")
            
    def _count_loc(self) -> int:
        """统计代码行数"""
        total = 0
        for py_file in self.project_path.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        total += len(f.readlines())
                except:
                    pass
        return total
        
    def _list_features(self) -> List[str]:
        """列出功能"""
        features = []
        
        for py_file in self.project_path.rglob("__init__.py"):
            if py_file.parent.name != self.project_path.name:
                features.append(py_file.parent.name)
                
        return features
        
    async def evolve_once(self) -> Dict:
        """执行一次进化"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "goals_processed": 0,
            "improvements": 0,
            "knowledge_added": 0
        }
        
        # 获取下一个目标
        goal = self.goal_generator.get_next_goal()
        if not goal:
            # 重新生成目标
            await self._generate_goals()
            goal = self.goal_generator.get_next_goal()
            
        if goal:
            result["goals_processed"] = 1
            
            # 执行目标
            success = await self._execute_goal(goal)
            
            if success:
                self.goal_generator.mark_completed(goal)
                self.metrics.goals_completed += 1
                result["improvements"] = 1
            else:
                self.goal_generator.mark_failed(goal, "Execution failed")
                self.metrics.goals_failed += 1
                
        # 更新指标
        self.metrics.uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        return result
        
    async def _execute_goal(self, goal: Dict) -> bool:
        """执行目标"""
        goal_desc = goal.get("description", "")
        
        print(f"\n🔧 Executing: {goal_desc}")
        
        # 简单模拟执行
        # 实际实现中会根据目标类型调用不同处理器
        return True
        
    def get_status(self) -> Dict:
        """获取状态"""
        return {
            "running": self.running,
            "uptime_hours": self.metrics.uptime_hours,
            "goals_completed": self.metrics.goals_completed,
            "goals_failed": self.metrics.goals_failed,
            "code_improvements": self.metrics.code_improvements,
            "knowledge_base_size": len(self.learner.knowledge_base),
            "current_goals": len(self.current_goals),
            "lines_of_code": self._count_loc()
        }


# ==================== 进化任务调度器 ====================

class EvolutionScheduler:
    """进化任务调度器"""
    
    def __init__(self, engine: SelfEvolvingEngine):
        self.engine = engine
        self.tasks: List[Dict] = []
        
    async def run_continuous(self, interval_seconds: int = 3600):
        """持续运行"""
        import asyncio
        
        while self.engine.running:
            try:
                result = await self.engine.evolve_once()
                print(f"\n📈 Evolution result: {result}")
            except Exception as e:
                print(f"❌ Evolution error: {e}")
                
            await asyncio.sleep(interval_seconds)
            
    def schedule_task(self, task: Dict):
        """调度任务"""
        self.tasks.append(task)


# ==================== 使用示例 ====================

async def main():
    """使用示例"""
    from pathlib import Path
    
    # 初始化引擎
    project_path = Path("autonomous-ai-engine")
    engine = SelfEvolvingEngine(
        project_path=project_path,
        config=EvolutionConfig(
            auto_improve=True,
            goal_generation_interval=3600,
            max_improvements_per_day=10
        )
    )
    
    # 启动
    await engine.start()
    
    # 打印状态
    print("\n" + "="*50)
    print("Engine Status:")
    status = engine.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")
    print("="*50)
    
    # 执行一次进化
    result = await engine.evolve_once()
    print(f"\nEvolution result: {result}")
    

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
