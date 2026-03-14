"""LLM Parser - 响应解析"""
import json
import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class ParseMode(Enum):
    AUTO = "auto"
    JSON = "json"
    MARKDOWN = "markdown"
    CODE = "code"
    TEXT = "text"

@dataclass
class ParsedResponse:
    """解析结果"""
    content: str
    mode: ParseMode
    data: Any
    confidence: float

class ResponseParser:
    """响应解析器"""
    
    def __init__(self):
        self.strategies = {
            ParseMode.JSON: self._parse_json,
            ParseMode.MARKDOWN: self._parse_markdown,
            ParseMode.CODE: self._parse_code,
            ParseMode.TEXT: self._parse_text,
        }
        
    def parse(self, response: str, mode: ParseMode = ParseMode.AUTO) -> ParsedResponse:
        """解析"""
        if mode == ParseMode.AUTO:
            mode = self._detect_mode(response)
            
        parser = self.strategies.get(mode, self._parse_text)
        data = parser(response)
        
        confidence = 0.9 if mode != ParseMode.TEXT else 0.5
        
        return ParsedResponse(
            content=response,
            mode=mode,
            data=data,
            confidence=confidence
        )
        
    def _detect_mode(self, response: str) -> ParseMode:
        """检测模式"""
        # JSON
        if response.strip().startswith(("{", "[")):
            try:
                json.loads(response)
                return ParseMode.JSON
            except:
                pass
                
        # 代码块
        if "```" in response:
            return ParseMode.CODE
            
        # Markdown
        if re.search(r'^#{1,6}\s+', response, re.MULTILINE):
            return ParseMode.MARKDOWN
            
        return ParseMode.TEXT
        
    def _parse_json(self, response: str) -> Any:
        """解析JSON"""
        try:
            return json.loads(response)
        except:
            # 尝试提取
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
        return response
        
    def _parse_markdown(self, response: str) -> Dict:
        """解析Markdown"""
        result = {
            "headings": [],
            "lists": [],
            "code_blocks": [],
            "text": response
        }
        
        result["headings"] = re.findall(r'^#{1,6}\s+(.+)$', response, re.MULTILINE)
        result["lists"] = re.findall(r'^[-*]\s+(.+)$', response, re.MULTILINE)
        result["code_blocks"] = re.findall(r'```[\s\S]*?```', response)
        
        return result
        
    def _parse_code(self, response: str) -> str:
        """解析代码"""
        matches = re.findall(r'```[\w]*\n([\s\S]*?)```', response)
        return matches[0] if matches else response
        
    def _parse_text(self, response: str) -> str:
        """解析文本"""
        return response.strip()
