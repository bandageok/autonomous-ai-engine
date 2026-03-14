
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
            "DEBUG": "\033[36m",    # 青色
            "INFO": "\033[32m",     # 绿色
            "WARNING": "\033[33m",  # 黄色
            "ERROR": "\033[31m",    # 红色
            "CRITICAL": "\033[35m", # 紫色
        }
        RESET = "\033[0m"
        
        def format(self, record):
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            return super().format(record)
            
    def get_logger(name: str, level: int = logging.INFO,
                   log_file: Optional[Path] = None) -> logging.Logger:
        """获取日志器"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
            
        # 控制台handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        
        formatter = ColoredFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S"
        )
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        # 文件handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            
            json_formatter = JSONFormatter()
            file_handler.setFormatter(json_formatter)
            logger.addHandler(file_handler)
            
        return logger
        
    class LogManager:
        """日志管理器"""
        
        def __init__(self, log_dir: Optional[Path] = None):
            self.log_dir = log_dir or Path("logs")
            self.loggers: dict = {}
            
        def get_logger(self, name: str) -> logging.Logger:
            """获取日志器"""
            if name not in self.loggers:
                log_file = self.log_dir / f"{name}.log"
                self.loggers[name] = get_logger(name, log_file=log_file)
            return self.loggers[name]
            
        def set_level(self, name: str, level: int):
            """设置日志级别"""
            if name in self.loggers:
                self.loggers[name].setLevel(level)


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
            "DEBUG": "\033[36m",    # 青色
            "INFO": "\033[32m",     # 绿色
            "WARNING": "\033[33m",  # 黄色
            "ERROR": "\033[31m",    # 红色
            "CRITICAL": "\033[35m", # 紫色
        }
        RESET = "\033[0m"
        
        def format(self, record):
            color = self.COLORS.get(record.levelname, "")
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            return super().format(record)
            
    def get_logger(name: str, level: int = logging.INFO,
                   log_file: Optional[Path] = None) -> logging.Logger:
        """获取日志器"""
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重复添加handler
        if logger.handlers:
            return logger
            
        # 控制台handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(level)
        
        formatter = ColoredFormatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%H:%M:%S"
        )
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        # 文件handler
        if log_file:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            
            json_formatter = JSONFormatter()
            file_handler.setFormatter(json_formatter)
            logger.addHandler(file_handler)
            
        return logger
        
    class LogManager:
        """日志管理器"""
        
        def __init__(self, log_dir: Optional[Path] = None):
            self.log_dir = log_dir or Path("logs")
            self.loggers: dict = {}
            
        def get_logger(self, name: str) -> logging.Logger:
            """获取日志器"""
            if name not in self.loggers:
                log_file = self.log_dir / f"{name}.log"
                self.loggers[name] = get_logger(name, log_file=log_file)
            return self.loggers[name]
            
        def set_level(self, name: str, level: int):
            """设置日志级别"""
            if name in self.loggers:
                self.loggers[name].setLevel(level)
