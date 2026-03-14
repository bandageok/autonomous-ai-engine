
    """Ollama Model Manager - 模型管理器"""
    import asyncio
    import json
    import subprocess
    from pathlib import Path
    from typing import Dict, List, Optional, Any
    import aiohttp
    
    class ModelInfo:
        """模型信息"""
        def __init__(self, name: str, size: int = 0, modified_at: str = ""):
            self.name = name
            self.size = size
            self.modified_at = modified_at
            self.status = "unknown"
            self.quantization = ""
            
        @classmethod
        def from_dict(cls, data: Dict):
            return cls(
                name=data.get("name", ""),
                size=data.get("size", 0),
                modified_at=data.get("modified_at", "")
            )
            
    class OllamaManager:
        """Ollama模型管理器"""
        
        def __init__(self, base_url: str = "http://localhost:11434"):
            self.base_url = base_url
            self.models: Dict[str, ModelInfo] = {}
            self.current_model: Optional[str] = None
            self.model_cache: Dict[str, Any] = {}
            
        async def list_models(self) -> List[ModelInfo]:
            """列出所有模型"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.base_url}/api/tags") as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            self.models = {
                                m["name"]: ModelInfo.from_dict(m) 
                                for m in data.get("models", [])
                            }
                            return list(self.models.values())
            except Exception as e:
                print(f"Error listing models: {e}")
            return []
            
        async def pull_model(self, model_name: str, progress_callback=None) -> bool:
            """拉取模型"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/api/pull",
                        json={"name": model_name, "stream": True}
                    ) as resp:
                        if resp.status == 200:
                            async for line in resp.content:
                                if progress_callback:
                                    data = json.loads(line)
                                    progress_callback(data)
                            return True
            except Exception as e:
                print(f"Error pulling model: {e}")
            return False
            
        async def generate(self, prompt: str, model: Optional[str] = None,
                          options: Optional[Dict] = None) -> str:
            """生成文本"""
            model = model or self.current_model
            if not model:
                return "Error: No model selected"
                
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False
            }
            
            if options:
                payload["options"] = options
                
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data.get("response", "")
            except Exception as e:
                return f"Error: {e}"
                
            return ""
            
        async def chat(self, messages: List[Dict], model: Optional[str] = None) -> str:
            """对话"""
            model = model or self.current_model
            if not model:
                return "Error: No model selected"
                
            payload = {
                "model": model,
                "messages": messages,
                "stream": False
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/api/chat",
                        json=payload
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data.get("message", {}).get("content", "")
            except Exception as e:
                return f"Error: {e}"
                
            return ""
            
        async def embed(self, text: str, model: Optional[str] = None) -> List[float]:
            """获取嵌入向量"""
            model = model or self.current_model
            if not model:
                return []
                
            payload = {
                "model": model,
                "prompt": text
            }
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.base_url}/api/embeddings",
                        json=payload
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            return data.get("embedding", [])
            except Exception as e:
                print(f"Error: {e}")
                
            return []
            
        def get_model_path(self, model_name: str) -> Path:
            """获取模型文件路径"""
            # 默认Ollama模型路径
            if Path.home().name == "OK bandage":
                return Path(f"C:/Users/OK bandage/.ollama/models/{model_name}")
            return Path.home() / ".ollama" / "models" / model_name
            
        def get_model_size(self, model_name: str) -> int:
            """获取模型大小(字节)"""
            path = self.get_model_path(model_name)
            if path.exists():
                if path.is_file():
                    return path.stat().st_size
                return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            return 0
            
        async def delete_model(self, model_name: str) -> bool:
            """删除模型"""
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.delete(
                        f"{self.base_url}/api/delete",
                        json={"name": model_name}
                    ) as resp:
                        return resp.status == 200
            except:
                return False
                
        def select_model(self, model_name: str):
            """选择当前模型"""
            if model_name in self.models:
                self.current_model = model_name
                return True
            return False
