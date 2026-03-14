
    """Utility Helpers - 通用工具函数"""
    import os
    import json
    import hashlib
    import uuid
    from pathlib import Path
    from typing import Any, Dict, List, Optional
    from datetime import datetime, timedelta
    import re
    
    def generate_id(prefix: str = "") -> str:
        """生成唯一ID"""
        unique = str(uuid.uuid4())[:8]
        return f"{prefix}{unique}" if prefix else unique
        
    def hash_text(text: str, algorithm: str = "md5") -> str:
        """文本哈希"""
        if algorithm == "md5":
            return hashlib.md5(text.encode()).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(text.encode()).hexdigest()
        return text
        
    def ensure_dir(path: Path):
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)
        
    def read_json(path: Path) -> Dict:
        """读取JSON"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def write_json(data: Any, path: Path, indent: int = 2):
        """写入JSON"""
        ensure_dir(path.parent)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            
    def format_time(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """格式化时间"""
        dt = dt or datetime.now()
        return dt.strftime(fmt)
        
    def parse_time(time_str: str) -> Optional[datetime]:
        """解析时间字符串"""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except:
                continue
        return None
        
    def time_ago(dt: datetime) -> str:
        """相对时间"""
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365}年前"
        elif diff.days > 30:
            return f"{diff.days // 30}个月前"
        elif diff.days > 0:
            return f"{diff.days}天前"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}小时前"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}分钟前"
        else:
            return "刚刚"
            
    def truncate(text: str, max_len: int = 100, suffix: str = "...") -> str:
        """截断文本"""
        if len(text) <= max_len:
            return text
        return text[:max_len - len(suffix)] + suffix
        
    def clean_text(text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除非打印字符
        text = ''.join(char for char in text if char.isprintable())
        return text.strip()
        
    def extract_urls(text: str) -> List[str]:
        """提取URL"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
        
    def extract_emails(text: str) -> List[str]:
        """提取邮箱"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text)
        
    def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """分块列表"""
        return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]
        
    def flatten(lst: List[Any]) -> List[Any]:
        """扁平化"""
        result = []
        for item in lst:
            if isinstance(item, list):
                result.extend(flatten(item))
            else:
                result.append(item)
        return result
        
    def retry(max_attempts: int = 3, delay: float = 1.0):
        """重试装饰器"""
        import functools
        import time
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            time.sleep(delay)
                        else:
                            raise
            return wrapper
        return decorator
        
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """限制范围"""
        return max(min_val, min(max_val, value))
        
    def percentage(part: float, total: float) -> float:
        """百分比计算"""
        if total == 0:
            return 0
        return (part / total) * 100


    """Utility Helpers - 通用工具函数"""
    import os
    import json
    import hashlib
    import uuid
    from pathlib import Path
    from typing import Any, Dict, List, Optional
    from datetime import datetime, timedelta
    import re
    
    def generate_id(prefix: str = "") -> str:
        """生成唯一ID"""
        unique = str(uuid.uuid4())[:8]
        return f"{prefix}{unique}" if prefix else unique
        
    def hash_text(text: str, algorithm: str = "md5") -> str:
        """文本哈希"""
        if algorithm == "md5":
            return hashlib.md5(text.encode()).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(text.encode()).hexdigest()
        return text
        
    def ensure_dir(path: Path):
        """确保目录存在"""
        path.mkdir(parents=True, exist_ok=True)
        
    def read_json(path: Path) -> Dict:
        """读取JSON"""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def write_json(data: Any, path: Path, indent: int = 2):
        """写入JSON"""
        ensure_dir(path.parent)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            
    def format_time(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """格式化时间"""
        dt = dt or datetime.now()
        return dt.strftime(fmt)
        
    def parse_time(time_str: str) -> Optional[datetime]:
        """解析时间字符串"""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%H:%M:%S"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except:
                continue
        return None
        
    def time_ago(dt: datetime) -> str:
        """相对时间"""
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 365:
            return f"{diff.days // 365}年前"
        elif diff.days > 30:
            return f"{diff.days // 30}个月前"
        elif diff.days > 0:
            return f"{diff.days}天前"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}小时前"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}分钟前"
        else:
            return "刚刚"
            
    def truncate(text: str, max_len: int = 100, suffix: str = "...") -> str:
        """截断文本"""
        if len(text) <= max_len:
            return text
        return text[:max_len - len(suffix)] + suffix
        
    def clean_text(text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除非打印字符
        text = ''.join(char for char in text if char.isprintable())
        return text.strip()
        
    def extract_urls(text: str) -> List[str]:
        """提取URL"""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return re.findall(url_pattern, text)
        
    def extract_emails(text: str) -> List[str]:
        """提取邮箱"""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text)
        
    def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """分块列表"""
        return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]
        
    def flatten(lst: List[Any]) -> List[Any]:
        """扁平化"""
        result = []
        for item in lst:
            if isinstance(item, list):
                result.extend(flatten(item))
            else:
                result.append(item)
        return result
        
    def retry(max_attempts: int = 3, delay: float = 1.0):
        """重试装饰器"""
        import functools
        import time
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt < max_attempts - 1:
                            time.sleep(delay)
                        else:
                            raise
            return wrapper
        return decorator
        
    def clamp(value: float, min_val: float, max_val: float) -> float:
        """限制范围"""
        return max(min_val, min(max_val, value))
        
    def percentage(part: float, total: float) -> float:
        """百分比计算"""
        if total == 0:
            return 0
        return (part / total) * 100
