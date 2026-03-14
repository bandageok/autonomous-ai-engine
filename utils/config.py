
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
                "mcp_server_port": self.mcp_server_port
            }
            
        @classmethod
        def from_dict(cls, data: Dict) -> "AppConfig":
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            
    class ConfigManager:
        """配置管理器"""
        
        def __init__(self, config_file: Optional[Path] = None):
            self.config_file = config_file or Path("config.json")
            self.config: AppConfig = AppConfig()
            self._load()
            
        def _load(self):
            """加载配置"""
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = AppConfig.from_dict(data)
                    
        def _save(self):
            """保存配置"""
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)
                
        def get(self, key: str, default: Any = None) -> Any:
            """获取配置"""
            return getattr(self.config, key, default)
            
        def set(self, key: str, value: Any):
            """设置配置"""
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self._save()
                
        def update(self, data: Dict):
            """批量更新"""
            for key, value in data.items():
                self.set(key, value)
                
        def reset(self):
            """重置为默认"""
            self.config = AppConfig()
            self._save()


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
                "mcp_server_port": self.mcp_server_port
            }
            
        @classmethod
        def from_dict(cls, data: Dict) -> "AppConfig":
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            
    class ConfigManager:
        """配置管理器"""
        
        def __init__(self, config_file: Optional[Path] = None):
            self.config_file = config_file or Path("config.json")
            self.config: AppConfig = AppConfig()
            self._load()
            
        def _load(self):
            """加载配置"""
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.config = AppConfig.from_dict(data)
                    
        def _save(self):
            """保存配置"""
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config.to_dict(), f, ensure_ascii=False, indent=2)
                
        def get(self, key: str, default: Any = None) -> Any:
            """获取配置"""
            return getattr(self.config, key, default)
            
        def set(self, key: str, value: Any):
            """设置配置"""
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                self._save()
                
        def update(self, data: Dict):
            """批量更新"""
            for key, value in data.items():
                self.set(key, value)
                
        def reset(self):
            """重置为默认"""
            self.config = AppConfig()
            self._save()
