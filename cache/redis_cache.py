"""Cache - 缓存系统"""
from typing import Dict, List, Optional, Any
from collections import OrderedDict
import time
import json
import hashlib

class CacheEntry:
    """缓存条目"""
    def __init__(self, key: str, value: Any, ttl: Optional[int] = None):
        self.key = key
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()
        self.access_count = 0
        
    def is_expired(self):
        """检查过期"""
        return self.ttl and time.time() - self.created_at > self.ttl

class LRUCache:
    """LRU缓存"""
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        
    def get(self, key: str) -> Any:
        """获取缓存"""
        if key not in self.cache:
            return None
        entry = self.cache[key]
        if entry.is_expired():
            del self.cache[key]
            return None
        self.cache.move_to_end(key)
        entry.access_count += 1
        return entry.value
        
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """设置缓存"""
        ttl = ttl or self.default_ttl
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)
        self.cache[key] = CacheEntry(key, value, ttl)
        
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False
        
    def clear(self):
        """清空缓存"""
        self.cache.clear()
        
    def stats(self) -> Dict:
        """获取统计"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "total_accesses": sum(e.access_count for e in self.cache.values())
        }
