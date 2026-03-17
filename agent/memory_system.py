"""Memory System - 记忆系统"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import hashlib
from collections import OrderedDict


class MemoryType:
    """记忆类型"""
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"
    WORKING = "working"


class MemoryItem:
    """记忆单元"""

    def __init__(self, content: str, memory_type: str, importance: float = 0.5):
        self.id = hashlib.md5(content.encode()).hexdigest()[:12]
        self.content = content
        self.type = memory_type
        self.importance = importance
        self.access_count = 0
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.tags = []
        self.metadata = {}

    def access(self):
        """访问记忆"""
        self.access_count += 1
        self.last_accessed = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "type": self.type,
            "importance": self.importance,
            "access_count": self.access_count,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "tags": self.tags,
            "metadata": self.metadata
        }


class MemoryStore:
    """记忆存储"""

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self.store: OrderedDict[str, MemoryItem] = OrderedDict()
        self.index_by_type: Dict[str, List[str]] = {}
        self.index_by_tag: Dict[str, List[str]] = {}

    def add(self, item: MemoryItem):
        """添加记忆"""
        if len(self.store) >= self.max_size:
            # 删除最旧的记忆
            oldest = next(iter(self.store))
            del self.store[oldest]

        self.store[item.id] = item

        # 更新索引
        if item.type not in self.index_by_type:
            self.index_by_type[item.type] = []
        self.index_by_type[item.type].append(item.id)

        for tag in item.tags:
            if tag not in self.index_by_tag:
                self.index_by_tag[tag] = []
            self.index_by_tag[tag].append(item.id)

    def get(self, item_id: str) -> Optional[MemoryItem]:
        """获取记忆"""
        item = self.store.get(item_id)
        if item:
            item.access()
        return item

    def search_by_type(self, memory_type: str) -> List[MemoryItem]:
        """按类型搜索"""
        ids = self.index_by_type.get(memory_type, [])
        return [self.store[i] for i in ids if i in self.store]

    def search_by_tag(self, tag: str) -> List[MemoryItem]:
        """按标签搜索"""
        ids = self.index_by_tag.get(tag, [])
        return [self.store[i] for i in ids if i in self.store]

    def get_recent(self, n: int = 10) -> List[MemoryItem]:
        """获取最近的记忆"""
        return list(self.store.values())[-n:]
