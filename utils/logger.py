"""Logger - 日志系统"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import json


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """彩色格式化器"""
    
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


class LogManager:
    """日志管理器"""
    
    def __init__(self, name: str = "AIEngine", level: str = "INFO"):
        self.name = name
        self.level = getattr(logging, level.upper())
        self.logger = logging.getLogger(name)
        self.logger.setLevel(self.level)
        
        # 清除已有的handlers
        self.logger.handlers.clear()
        
        # 添加控制台handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(self.level)
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console.setFormatter(formatter)
        self.logger.addHandler(console)
    
    def add_file_handler(self, path: str, level: Optional[str] = None):
        """添加文件handler"""
        log_path = Path(path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setLevel(getattr(logging, (level or "INFO").upper()))
        
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def set_level(self, level: str):
        """设置日志级别"""
        self.level = getattr(logging, level.upper())
        self.logger.setLevel(self.level)


# 全局日志实例
_default_logger: Optional[LogManager] = None


def get_logger(name: str = "AIEngine") -> logging.Logger:
    """获取日志器"""
    global _default_logger
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        if _default_logger is None:
            _default_logger = LogManager(name)
        logger.addHandler(_default_logger.logger.handlers[0])
    
    return logger


def setup_logging(name: str = "AIEngine", level: str = "INFO", log_file: Optional[str] = None):
    """设置日志"""
    global _default_logger
    
    _default_logger = LogManager(name, level)
    
    if log_file:
        _default_logger.add_file_handler(log_file)
    
    return _default_logger.logger
