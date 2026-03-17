"""Configuration - 配置管理"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    """应用配置"""
    app_name: str = "AIEngine"
    version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # API配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # 数据库
    db_path: str = "./data/app.db"
    
    # Ollama
    ollama_url: str = "http://localhost:11434"
    default_model: str = "qwen2.5:7b"
    
    # 向量存储
    vector_store_path: str = "./data/vectors"
    
    # 任务配置
    max_concurrent_tasks: int = 5
    task_timeout: int = 300
    
    # MCP配置
    mcp_server_port: int = 8765
    
    def to_dict(self) -> Dict:
        return {
            "app_name": self.app_name,
            "version": self.version,
            "debug": self.debug,
            "log_level": self.log_level,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "db_path": self.db_path,
            "ollama_url": self.ollama_url,
            "default_model": self.default_model,
            "vector_store_path": self.vector_store_path,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "task_timeout": self.task_timeout,
            "mcp_server_port": self.mcp_server_port,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AppConfig":
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})
    
    def save(self, path: str = "config.json"):
        """保存配置"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: str = "config.json") -> "AppConfig":
        """加载配置"""
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return cls.from_dict(json.load(f))
        return cls()


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config.json"
        self.config: AppConfig = AppConfig.load(self.config_path)
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        return getattr(self.config, key, default)
    
    def set(self, key: str, value: Any):
        """设置配置"""
        setattr(self.config, key, value)
    
    def save(self):
        """保存配置"""
        self.config.save(self.config_path)
    
    def reload(self):
        """重新加载配置"""
        self.config = AppConfig.load(self.config_path)
