"""LLM Prompt - 提示词管理"""
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

@dataclass
class PromptTemplate:
    """提示词模板"""
    name: str
    template: str
    description: str = ""
    variables: List[str] = None
    
    def __post_init__(self):
        if self.variables is None:
            import re
            self.variables = re.findall(r'\{(\w+)\}', self.template)
            
    def render(self, **kwargs) -> str:
        """渲染"""
        result = self.template
        for var in self.variables:
            value = kwargs.get(var, f"{{{var}}}")
            result = result.replace(f"{{{var}}}", str(value))
        return result

class PromptLibrary:
    """提示词库"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
        self._init_builtins()
        
    def _init_builtins(self):
        """初始化内置模板"""
        self.templates["system"] = PromptTemplate(
            name="system",
            template="You are a helpful AI assistant.",
            description="System prompt"
        )
        
        self.templates["summarize"] = PromptTemplate(
            name="summarize",
            template="Summarize the following:\n{content}",
            description="Summarization"
        )
        
        self.templates["analyze"] = PromptTemplate(
            name="analyze",
            template="Analyze this:\n{content}\n\nProvide: 1) Key points, 2) Issues, 3) Recommendations",
            description="Analysis"
        )
        
        self.templates["code_review"] = PromptTemplate(
            name="code_review",
            template="Review this code:\n```{language}\n{code}\n```\n\nCheck for: bugs, style, performance, security",
            description="Code review"
        )
        
    def add(self, template: PromptTemplate):
        """添加模板"""
        self.templates[template.name] = template
        
    def get(self, name: str) -> Optional[PromptTemplate]:
        """获取模板"""
        return self.templates.get(name)
        
    def render(self, name: str, **kwargs) -> str:
        """渲染模板"""
        template = self.get(name)
        return template.render(**kwargs) if template else ""

class PromptOptimizer:
    """提示词优化器"""
    
    def __init__(self):
        self.rules = []
        
    def optimize(self, prompt: str) -> str:
        """优化"""
        result = prompt
        
        # 移除多余空白
        result = "\n".join(line.strip() for line in result.split("\n") if line.strip())
        
        # 添加格式提示
        if "请" in result and "格式" not in result:
            result += "\n\nProvide clear, structured output."
            
        return result
