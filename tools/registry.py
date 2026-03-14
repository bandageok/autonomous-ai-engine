"""Tools Registry - 工具注册表"""
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass
import inspect
import json

@dataclass
class Tool:
    """工具"""
    name: str
    description: str
    func: Callable
    parameters: Dict
    category: str = "general"

class ToolsRegistry:
    """工具注册表"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.categories: Dict[str, List[str]] = {}
        
    def register(self, name: str, description: str, func: Callable,
                 category: str = "general") -> Tool:
        """注册工具"""
        params = self._extract_params(func)
        
        tool = Tool(
            name=name,
            description=description,
            func=func,
            parameters=params,
            category=category
        )
        
        self.tools[name] = tool
        
        if category not in self.categories:
            self.categories[category] = []
        self.categories[category].append(name)
        
        return tool
        
    def _extract_params(self, func: Callable) -> Dict:
        """提取参数"""
        sig = inspect.signature(func)
        params = {}
        
        for name, param in sig.parameters.items():
            params[name] = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "any",
                "required": param.default == inspect.Parameter.empty,
                "default": str(param.default) if param.default != inspect.Parameter.empty else None
            }
            
        return params
        
    def get(self, name: str) -> Optional[Tool]:
        """获取工具"""
        return self.tools.get(name)
        
    def list_by_category(self, category: str) -> List[Tool]:
        """按类别列出"""
        names = self.categories.get(category, [])
        return [self.tools[n] for n in names]
        
    def search(self, query: str) -> List[Tool]:
        """搜索"""
        results = []
        query_lower = query.lower()
        
        for tool in self.tools.values():
            if query_lower in tool.name.lower() or query_lower in tool.description.lower():
                results.append(tool)
                
        return results
        
    def execute(self, name: str, **kwargs) -> Any:
        """执行工具"""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")
            
        return tool.func(**kwargs)
