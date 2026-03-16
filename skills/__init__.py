"""Skills System - 技能系统
类似OpenClaw的Skill框架，支持技能注册、发现和执行
"""
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
import importlib.util
import inspect
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    handler: Callable
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    
    def execute(self, **kwargs) -> Any:
        """执行技能"""
        return self.handler(**kwargs)
    
    def validate_params(self, params: Dict) -> bool:
        """验证参数"""
        required = self.parameters.get("required", [])
        return all(k in params for k in required)


class SkillRegistry:
    """技能注册中心"""
    
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self.tags_index: Dict[str, List[str]] = {}
        
    def register(self, skill: Skill):
        """注册技能"""
        self.skills[skill.name] = skill
        
        # 更新标签索引
        for tag in skill.tags:
            if tag not in self.tags_index:
                self.tags_index[tag] = []
            self.tags_index[tag].append(skill.name)
    
    def get(self, name: str) -> Optional[Skill]:
        """获取技能"""
        return self.skills.get(name)
    
    def list_all(self) -> List[Skill]:
        """列出所有技能"""
        return list(self.skills.values())
    
    def search_by_tag(self, tag: str) -> List[Skill]:
        """按标签搜索"""
        skill_names = self.tags_index.get(tag, [])
        return [self.skills[name] for name in skill_names if name in self.skills]
    
    def search_by_keyword(self, keyword: str) -> List[Skill]:
        """关键词搜索"""
        keyword = keyword.lower()
        results = []
        for skill in self.skills.values():
            if (keyword in skill.name.lower() or 
                keyword in skill.description.lower()):
                results.append(skill)
        return results
    
    def load_from_directory(self, skills_dir: Path):
        """从目录加载技能"""
        if not skills_dir.exists():
            return
        
        for py_file in skills_dir.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            try:
                self._load_skill_file(py_file)
            except Exception as e:
                print(f"Error loading skill {py_file}: {e}")
    
    def _load_skill_file(self, file_path: Path):
        """加载技能文件"""
        spec = importlib.util.spec_from_file_location("skill_module", file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找 Skill 类并注册
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj) and hasattr(obj, "handler"):
                    if hasattr(obj, "name") and hasattr(obj, "description"):
                        skill = obj()
                        self.register(skill)


class SkillExecutor:
    """技能执行器"""
    
    def __init__(self, registry: SkillRegistry):
        self.registry = registry
        self.execution_history: List[Dict] = []
    
    def execute(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """执行技能"""
        skill = self.registry.get(skill_name)
        
        if not skill:
            return {
                "success": False,
                "error": f"Skill '{skill_name}' not found"
            }
        
        if not skill.validate_params(kwargs):
            return {
                "success": False,
                "error": "Invalid parameters"
            }
        
        try:
            start_time = datetime.now()
            result = skill.execute(**kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            record = {
                "skill": skill_name,
                "params": kwargs,
                "result": result,
                "duration": duration,
                "timestamp": start_time.isoformat()
            }
            self.execution_history.append(record)
            
            return {
                "success": True,
                "result": result,
                "duration": duration
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取执行历史"""
        return self.execution_history[-limit:]


# 全局技能注册表
_global_registry = SkillRegistry()


def register_skill(name: str, description: str, tags: List[str] = None):
    """装饰器：注册技能"""
    def decorator(func: Callable):
        skill = Skill(
            name=name,
            description=description,
            handler=func,
            tags=tags or []
        )
        _global_registry.register(skill)
        return func
    return decorator


def get_registry() -> SkillRegistry:
    """获取全局注册表"""
    return _global_registry


def get_executor() -> SkillExecutor:
    """获取全局执行器"""
    return SkillExecutor(_global_registry)
