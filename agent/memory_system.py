
    """Memory System - 记忆系统"""
    from typing import Dict, List, Optional, Any
    from datetime import datetime, timedelta
    import json
    import hashlib
    from collections import OrderedDict
    
    class MemoryType:
        """记忆类型"""
        EPISODIC = "episodic"      # 情景记忆
        SEMANTIC = "semantic"       # 语义记忆
        PROCEDURAL = "procedural"   # 程序记忆
        WORKING = "working"         # 工作记忆
        
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
            # 容量检查
            if len(self.store) >= self.max_size:
                self._evict_oldest()
                
            self.store[item.id] = item
            
            # 更新索引
            if item.type not in self.index_by_type:
                self.index_by_type[item.type] = []
            self.index_by_type[item.type].append(item.id)
            
            for tag in item.tags:
                if tag not in self.index_by_tag:
                    self.index_by_tag[tag] = []
                self.index_by_tag[tag].append(item.id)
                
        def get(self, memory_id: str) -> Optional[MemoryItem]:
            """获取记忆"""
            if memory_id in self.store:
                item = self.store[memory_id]
                item.access()
                return item
            return None
            
        def search(self, query: str, memory_type: Optional[str] = None) -> List[MemoryItem]:
            """搜索记忆"""
            results = []
            query_lower = query.lower()
            
            for item in self.store.values():
                if memory_type and item.type != memory_type:
                    continue
                    
                if query_lower in item.content.lower():
                    results.append(item)
                    
            # 按重要性排序
            results.sort(key=lambda x: (x.importance, x.access_count), reverse=True)
            
            return results[:10]
            
        def _evict_oldest(self):
            """驱逐最老的记忆"""
            if self.store:
                oldest_id = next(iter(self.store))
                item = self.store[oldest_id]
                
                # 从索引中移除
                if item.type in self.index_by_type:
                    self.index_by_type[item.type].remove(oldest_id)
                    
                for tag in item.tags:
                    if tag in self.index_by_tag:
                        self.index_by_tag[tag].remove(oldest_id)
                        
                del self.store[oldest_id]
                
        def get_stats(self) -> Dict:
            """获取统计信息"""
            return {
                "total_memories": len(self.store),
                "by_type": {t: len(ids) for t, ids in self.index_by_type.items()},
                "by_tag": {tag: len(ids) for tag, ids in self.index_by_tag.items()},
                "avg_importance": sum(i.importance for i in self.store.values()) / max(len(self.store), 1)
            }
            
    class MemorySystem:
        """统一记忆系统"""
        
        def __init__(self):
            self.short_term = MemoryStore(max_size=100)      # 短期记忆
            self.long_term = MemoryStore(max_size=10000)     # 长期记忆
            self.working_memory: Dict[str, Any] = {}
            
        def remember(self, content: str, memory_type: str = MemoryType.EPISODIC, 
                     importance: float = 0.5, tags: Optional[List[str]] = None):
            """记忆存储"""
            item = MemoryItem(content, memory_type, importance)
            if tags:
                item.tags = tags
                
            if memory_type == MemoryType.WORKING:
                self.working_memory[content[:100]] = item
            elif memory_type == MemoryType.EPISODIC:
                self.short_term.add(item)
            else:
                self.long_term.add(item)
                
        def recall(self, query: str, memory_type: Optional[str] = None) -> List[MemoryItem]:
            """记忆检索"""
            # 先查短期，再查长期
            results = self.short_term.search(query, memory_type)
            
            if not results:
                results = self.long_term.search(query, memory_type)
                
            return results
            
        def consolidate(self):
            """记忆整合 - 将短期记忆转入长期"""
            for item in list(self.short_term.store.values()):
                if item.access_count > 3 or item.importance > 0.7:
                    self.long_term.add(item)
                    del self.short_term.store[item.id]
                    
        def get_context(self, max_items: int = 5) -> str:
            """获取当前上下文"""
            recent = sorted(
                self.short_term.store.values(),
                key=lambda x: x.last_accessed,
                reverse=True
            )[:max_items]
            
            return "\n".join([item.content for item in recent])
