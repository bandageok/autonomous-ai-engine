```python
import asyncio
import aioredis
from collections import OrderedDict
from typing import Optional, Dict, Any, AsyncGenerator, AsyncContextManager
from datetime import timedelta
from cryptography.fernet import Fernet
import logging

logging.basicConfig(level=logging.INFO)

class CryptoUtil:
    """
    加密工具类，用于敏感数据的加密和解密
    """
    def __init__(self, key: str):
        """
        初始化加密工具
        :param key: 密钥，用于Fernet加密
        """
        self.key = key.encode()

    async def encrypt(self, data: str) -> bytes:
        """
        加密数据
        :param data: 待加密的字符串
        :return: 加密后的字节数据
        """
        fernet = Fernet(self.key)
        return fernet.encrypt(data.encode())

    async def decrypt(self, data: bytes) -> str:
        """
        解密数据
        :param data: 待解密的字节数据
        :return: 解密后的字符串
        """
        fernet = Fernet(self.key)
        return fernet.decrypt(data).decode()

class MemoryCache:
    """
    内存缓存实现，采用LRU策略
    """
    def __init__(self, max_size: int):
        """
        初始化内存缓存
        :param max_size: 最大缓存条目数
        """
        self.max_size = max_size
        self._cache = OrderedDict()

    async def get(self, key: str) -> Optional[str]:
        """
        获取缓存项
        :param key: 缓存键
        :return: 缓存值或None
        """
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    async def set(self, key: str, value: str):
        """
        设置缓存项
        :param key: 缓存键
        :param value: 缓存值
        """
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
        self._cache[key] = value

    async def delete(self, key: str):
        """
        删除缓存项
        :param key: 缓存键
        """
        if key in self._cache:
            del self._cache[key]

class RedisCache:
    """
    Redis分布式缓存实现
    """
    def __init__(self, redis_url: str, ttl: int):
        """
        初始化Redis缓存
        :param redis_url: Redis连接地址
        :param ttl: 缓存时间到 (秒)
        """
        self.redis_url = redis_url
        self.ttl = ttl
        self.pool = None

    async def connect(self):
        """
        连接到Redis服务器
        """
        self.pool = await aioredis.create_pool(self.redis_url)

    async def get(self, key: str) -> Optional[str]:
        """
        获取缓存项
        :param key: 缓存键
        :return: 缓存值或None
        """
        data = await self.pool.get(key)
        if data is not None:
            return await self.decrypt(data)
        return None

    async def set(self, key: str, value: str):
        """
        设置缓存项
        :param key: 缓存键
        :param value: 缓存值
        """
        encrypted = await self.encrypt(value)
        await self.pool.set(key, encrypted)
        await self.pool.expire(key, self.ttl)

    async def delete(self, key: str):
        """
        删除缓存项
        :param key: 缓存键
        """
        await self.pool.delete(key)

    async def encrypt(self, data: str) -> bytes:
        """
        加密数据
        :param data: 待加密的字符串
        :return: 加密后的字节数据
        """
        return Fernet(b'your-secret-key-123').encrypt(data.encode())

    async def decrypt(self, data: bytes) -> str:
        """
        解密数据
        :param data: 待解密的字节数据
        :return: 解密后的字符串
        """
        return Fernet(b'your-secret-key-123').decrypt(data).decode()

class CacheSystem:
    """
    综合缓存系统，整合内存和Redis缓存
    """
    def __init__(self, memory_max_size: int, redis_url: str, redis_ttl: int):
        """
        初始化缓存系统
        :param memory_max_size: 内存缓存最大条目数
        :param redis_url: Redis连接地址
        :param redis_ttl: Redis缓存时间到 (秒)
        """
        self.memory_cache = MemoryCache(memory_max_size)
        self.redis_cache = RedisCache(redis_url, redis_ttl)
        self.hit_count = 0
        self.miss_count = 0
        self._lock = asyncio.Lock()

    async def init(self):
        """
        初始化缓存系统，建立Redis连接
        """
        await self.redis_cache.connect()
        await self.preheat_cache()

    async def preheat_cache(self):
        """
        预加载数据到缓存
        """
        # 示例：预加载一些数据
        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        for key, value in data.items():
            await self.set(key, value)

    async def get(self, key: str) -> Optional[str]:
        """
        获取缓存项
        :param key: 缓存键
        :return: 缓存值或None
        """
        async with self._lock:
            # 优先从内存缓存获取
            data = await self.memory_cache.get(key)
            if data is not None:
                self.hit_count += 1
                return data
            # 否则从Redis获取
            data = await self.redis_cache.get(key)
            if data is not None:
                self.hit_count += 1
                await self.memory_cache.set(key, data)
                return data
            self.miss_count += 1
            return None

    async def set(self, key: str, value: str):
        """
        设置缓存项
        :param key: 缓存键
        :param value: 缓存值
        """
        await self.memory_cache.set(key, value)
        await self.redis_cache.set(key, value)

    async def delete(self, key: str):
        """
        删除缓存项
        :param key: 缓存键
        """
        await self.memory_cache.delete(key)
        await self.redis_cache.delete(key)

    def get_hit_rate(self) -> float:
        """
        获取缓存命中率
        :return: 命中率 (0.0-1.0)
        """
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return self.hit_count / total

    async def __aenter__(self):
        """
        异步上下文管理器入口
        """
        await self.init()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器出口
        """
        await self.redis_cache.pool.close()
```