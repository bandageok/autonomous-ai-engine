"""Core Memory - 记忆系统"""
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import uuid

@dataclass
class MemoryItem:
    """记忆条目"""
    id: str
    content: str
    memory_type: str  # episodic, semantic, procedural
    importance: float  # 0-1
    created_at: datetime
    accessed_at: datetime
    access_count: int = 0
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class MemoryIndex:
    """记忆索引"""
    def __init__(self):
        self.by_type: Dict[str, List[str]] = {}
        self.by_tag: Dict[str, List[str]] = {}
        self.by_importance: List[str] = []
        
    def add(self, item: MemoryItem):
        """添加索引"""
        # 按类型
        if item.memory_type not in self.by_type:
            self.by_type[item.memory_type] = []
        self.by_type[item.memory_type].append(item.id)
        
        # 按标签
        for tag in item.tags:
            if tag not in self.by_tag:
                self.by_tag[tag] = []
            self.by_tag[tag].append(item.id)
            
    def remove(self, item_id: str, item: MemoryItem):
        """移除索引"""
        if item.memory_type in self.by_type:
            if item_id in self.by_type[item.memory_type]:
                self.by_type[item.memory_type].remove(item_id)
                
        for tag in item.tags:
            if tag in self.by_tag:
                if item_id in self.by_tag[tag]:
                    self.by_tag[tag].remove(item_id)

class MemorySystem:
    """记忆系统"""
    
    def __init__(self, max_items: int = 10000):
        self.max_items = max_items
        self.memories: Dict[str, MemoryItem] = {}
        self.index = MemoryIndex()
        
    def store(self, content: str, memory_type: str = "episodic",
              importance: float = 0.5, tags: List[str] = None,
              metadata: Dict = None) -> str:
        """存储记忆"""
        # 容量检查
        if len(self.memories) >= self.max_items:
            self._evict()
            
        memory_id = str(uuid.uuid4())
        
        now = datetime.now()
        item = MemoryItem(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            created_at=now,
            accessed_at=now,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self.memories[memory_id] = item
        self.index.add(item)
        
        return memory_id
        
    def recall(self, query: str, memory_type: str = None,
               tags: List[str] = None, limit: int = 10) -> List[MemoryItem]:
        """检索记忆"""
        results = []
        
        for item in self.memories.values():
            # 类型过滤
            if memory_type and item.memory_type != memory_type:
                continue
                
            # 标签过滤
            if tags and not any(tag in item.tags for tag in tags):
                continue
                
            # 内容匹配
            if query.lower() in item.content.lower():
                item.access_count += 1
                item.accessed_at = datetime.now()
                results.append(item)
                
        # 按重要性和访问次数排序
        results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
        
        return results[:limit]
        
    def _evict(self):
        """驱逐低重要性记忆"""
        if not self.memories:
            return
            
        # 找出最不重要的
        to_evict = min(
            self.memories.items(),
            key=lambda x: (x[1].importance, x[1].access_count, x[1].accessed_at)
        )
        
        del self.memories[to_evict[0]]
        self.index.remove(to_evict[0], to_evict[1])
        
    def get_stats(self) -> Dict:
        """获取统计"""
        by_type = {}
        for item in self.memories.values():
            by_type[item.memory_type] = by_type.get(item.memory_type, 0) + 1
            
        return {
            "total": len(self.memories),
            "by_type": by_type,
            "avg_importance": sum(m.importance for m in self.memories.values()) / max(len(self.memories), 1)
        }
