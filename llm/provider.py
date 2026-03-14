"""LLM Provider - LLM提供者"""
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import json

class BaseLLM(ABC):
    """LLM基类"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        pass

class OllamaLLM(BaseLLM):
    """Ollama LLM"""
    
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "qwen2.5:7b"):
        self.base_url = base_url
        self.model = model
        self.default_options = {
            "temperature": 0.7,
            "num_predict": 2048,
        }
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成"""
        options = {**self.default_options, **kwargs}
        
        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False,
            "options": options
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", 
                                       json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("response", "")
        except Exception as e:
            return f"Error: {e}"
            
        return ""
    
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """对话"""
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "stream": False
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/chat",
                                       json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("message", {}).get("content", "")
        except Exception as e:
            return f"Error: {e}"
            
        return ""

class OpenAILLM(BaseLLM):
    """OpenAI LLM"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        
    async def generate(self, prompt: str, **kwargs) -> str:
        """生成"""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)
        
    async def chat(self, messages: List[Dict], **kwargs) -> str:
        """对话"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 2048)
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/chat/completions",
                                       json=payload, headers=headers) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error: {e}"
            
        return ""
