
    """Prompt Engine - 提示词引擎"""
    from typing import Dict, List, Optional, Any, Callable
    import re
    import json
    
    class PromptTemplate:
        """提示词模板"""
        
        def __init__(self, template: str, name: str = "", description: str = ""):
            self.template = template
            self.name = name
            self.description = description
            self.variables: List[str] = self._extract_variables()
            
        def _extract_variables(self) -> List[str]:
            """提取变量"""
            return re.findall(r'\{(\w+)\}', self.template)
            
        def render(self, **kwargs) -> str:
            """渲染模板"""
            result = self.template
            for var in self.variables:
                value = kwargs.get(var, f"{{{var}}}")
                result = result.replace(f"{{{var}}}", str(value))
            return result
            
        def validate(self, **kwargs) -> bool:
            """验证参数"""
            required = set(self.variables)
            provided = set(kwargs.keys())
            return required.issubset(provided)
            
    class PromptLibrary:
        """提示词库"""
        
        def __init__(self):
            self.templates: Dict[str, PromptTemplate] = {}
            self._init_default_templates()
            
        def _init_default_templates(self):
            """初始化默认模板"""
            defaults = {
                "summarize": PromptTemplate(
                    "请总结以下内容:\n{content}\n\n简洁概括要点:",
                    "总结",
                    "总结给定内容"
                ),
                "analyze": PromptTemplate(
                    "分析以下内容:\n{content}\n\n请从以下角度分析:\n1. 主要观点\n2. 潜在问题\n3. 改进建议",
                    "分析",
                    "深度分析内容"
                ),
                "code_review": PromptTemplate(
                    "代码审查请求:\n\n语言: {language}\n代码:\n```{language}\n{code}\n```\n\n请检查:\n1. Bug和潜在问题\n2. 代码风格\n3. 性能优化\n4. 安全问题",
                    "代码审查",
                    "审查代码质量"
                ),
                "translate": PromptTemplate(
                    "请将以下内容翻译成{target_language}:\n{content}",
                    "翻译",
                    "翻译内容"
                ),
                " brainstorm": PromptTemplate(
                    "头脑风暴: {topic}\n\n请列出至少10个创意想法:",
                    "头脑风暴",
                    "生成创意想法"
                )
            }
            
            self.templates.update(defaults)
            
        def add_template(self, name: str, template: PromptTemplate):
            """添加模板"""
            self.templates[name] = template
            
        def get_template(self, name: str) -> Optional[PromptTemplate]:
            """获取模板"""
            return self.templates.get(name)
            
        def render(self, name: str, **kwargs) -> Optional[str]:
            """渲染指定模板"""
            template = self.get_template(name)
            if template:
                return template.render(**kwargs)
            return None
            
    class PromptOptimizer:
        """提示词优化器"""
        
        def __init__(self):
            self.optimization_rules = [
                self._rule_clear_formatting,
                self._rule_add_examples,
                self._rule_specify_format,
                self._rule_set_constraints
            ]
            
        def optimize(self, prompt: str) -> str:
            """优化提示词"""
            result = prompt
            
            for rule in self.optimization_rules:
                result = rule(result)
                
            return result
            
        def _rule_clear_formatting(self, prompt: str) -> str:
            """清除格式问题"""
            # 移除多余空白
            lines = [line.strip() for line in prompt.split("\n")]
            return "\n".join([l for l in lines if l])
            
        def _rule_add_examples(self, prompt: str) -> str:
            """添加示例"""
            if "例如" not in prompt and "example" not in prompt.lower():
                # 简单添加示例提示
                prompt += "\n\n如有需要可提供示例。"
            return prompt
            
        def _rule_specify_format(self, prompt: str) -> str:
            """指定输出格式"""
            if "格式" not in prompt and "format" not in prompt.lower():
                if "请" in prompt:
                    prompt += "\n\n请按以下格式输出: {格式说明}"
            return prompt
            
        def _rule_set_constraints(self, prompt: str) -> str:
            """设置约束"""
            constraints = ["简洁", "准确", "实用"]
            
            if not any(c in prompt for c in constraints):
                prompt += "\n\n请保持简洁准确。"
                
            return prompt
            
    class PromptEngine:
        """统一提示词引擎"""
        
        def __init__(self):
            self.library = PromptLibrary()
            self.optimizer = PromptOptimizer()
            self.history: List[Dict] = []
            
        def create_prompt(self, template_name: str, **kwargs) -> str:
            """创建提示词"""
            prompt = self.library.render(template_name, **kwargs)
            
            if prompt:
                prompt = self.optimizer.optimize(prompt)
                self.history.append({
                    "template": template_name,
                    "params": kwargs,
                    "result": prompt
                })
                
            return prompt or ""
            
        def add_custom_template(self, name: str, template: str, description: str = ""):
            """添加自定义模板"""
            self.library.add_template(name, PromptTemplate(template, name, description))
