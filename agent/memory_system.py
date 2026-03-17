"""Memory System - 记忆系统"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import hashlib
from collections import OrderedDict, deque
import faiss
import numpy as np
import asyncio
from dataclasses import dataclass
from uuid import uuid4


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


# === Generated Extension: Vector Memory Index and Advanced Memory Management ===

@dataclass
class MemoryEntry:
    """记忆条目数据类，包含记忆内容、元数据和时间戳"""
    content: str
    metadata: Dict[str, Any]
    timestamp: datetime
    uuid: str


class VectorMemoryIndex:
    """基于FAISS的向量语义搜索索引，支持添加、搜索和删除记忆"""
    
    def __init__(self, dimension: int, nlist: int = 128):
        """初始化向量索引"""
        self.dimension = dimension
        self.nlist = nlist
        self.index = faiss.IndexFlatL2(dimension)
        self.vectors: List[np.ndarray] = []
        self.uuid_to_index: Dict[str, int] = {}
        self.lock = asyncio.Lock()
        
    async def add(self, vectors: List[np.ndarray], uuids: List[str]) -> None:
        """异步添加向量到索引"""
        async with self.lock:
            for vec, uuid in zip(vectors, uuids):
                index = len(self.vectors)
                self.vectors.append(vec)
                self.uuid_to_index[uuid] = index
                
            self.index.add(np.array(self.vectors))
            
    async def search(self, query_vector: np.ndarray, k: int = 5) -> List:
        """异步搜索最相似的向量"""
        async with self.lock:
            if not self.vectors:
                return []
                
            distances, indices = self.index.search(np.array([query_vector]), k)
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                uuid = list(self.uuid_to_index.keys())[list(self.uuid_to_index.values()).index(idx)]
                results.append((dist, uuid))
            return results
            
    async def delete(self, uuids: List[str]) -> None:
        """异步删除指定UUID的记忆"""
        async with self.lock:
            indices_to_remove = [self.uuid_to_index[uuid] for uuid in uuids]
            self.vectors = [vec for i, vec in enumerate(self.vectors) if i not in indices_to_remove]
            self.uuid_to_index = {uuid: idx for idx, uuid in enumerate(self.vectors, start=0)}
            self.index = faiss.IndexFlatL2(self.dimension)
            self.index.add(np.array(self.vectors))


class MemoryConsolidator:
    """将相似的片段记忆合并为更高层次的抽象"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        """初始化记忆合并器"""
        self.similarity_threshold = similarity_threshold
        self.memory_index = VectorMemoryIndex(dimension=768, nlist=128)
        
    def consolidate(self, memories: List[MemoryEntry]) -> List[MemoryEntry]:
        """合并相似的记忆条目"""
        if not memories:
            return []
            
        vectors = [self._vectorize(memory.content) for memory in memories]
        uuids = [str(uuid4()) for _ in memories]
        
        asyncio.run(self.memory_index.add(vectors, uuids))
        
        similar_pairs = self._find_similar_pairs(memories, vectors)
        
        consolidated = []
        merged = set()
        
        for pair in similar_pairs:
            if memories[pair[0]].uuid not in merged and memories[pair[1]].uuid not in merged:
                merged.add(memories[pair[0]].uuid)
                merged.add(memories[pair[1]].uuid)
                
                consolidated_content = self._merge_contents(memories[pair[0]].content, memories[pair[1]].content)
                consolidated_metadata = self._merge_metadata(memories[pair[0]].metadata, memories[pair[1]].metadata)
                
                consolidated.append(MemoryEntry(
                    content=consolidated_content,
                    metadata=consolidated_metadata,
                    timestamp=datetime.now(),
                    uuid=str(uuid4())
                ))
                
        return consolidated
    
    def _vectorize(self, text: str) -> np.ndarray:
        """将文本转换为向量表示（模拟）"""
        return np.random.rand(768).astype(np.float32)
    
    def _find_similar_pairs(self, memories: List[MemoryEntry], vectors: List[np.ndarray]) -> List:
        """查找相似的记忆对"""
        similar_pairs = []
        for i in range(len(memories)):
            for j in range(i+1, len(memories)):
                similarity = self._calculate_similarity(vectors[i], vectors[j])
                if similarity > self.similarity_threshold:
                    similar_pairs.append((i, j))
        return similar_pairs
    
    def _calculate_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算向量相似度"""
        return 1.0 - (np.linalg.norm(vec1 - vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))
    
    def _merge_contents(self, content1: str, content2: str) -> str:
        """合并两个记忆内容"""
        return f"{content1} [merged with] {content2}"
    
    def _merge_metadata(self, meta1: Dict, meta2: Dict) -> Dict:
        """合并元数据"""
        merged = meta1.copy()
        for k, v in meta2.items():
            if k in merged:
                if isinstance(merged[k], list) and isinstance(v, list):
                    merged[k] = merged[k] + v
                elif isinstance(merged[k], (int, float)) and isinstance(v, (int, float)):
                    merged[k] = merged[k] + v
            else:
                merged[k] = v
        return merged


class MemoryImportanceCalculator:
    """基于多种因素计算记忆重要性分数"""
    
    def __init__(self, recency_weight: float = 0.3, frequency_weight: float = 0.3, salience_weight: float = 0.4):
        """初始化计算器，设置各因素权重"""
        self.recency_weight = recency_weight
        self.frequency_weight = frequency_weight
        self.salience_weight = salience_weight
        
    def calculate(self, memory: MemoryItem, current_time: Optional[datetime] = None) -> float:
        """计算记忆的重要性分数"""
        if current_time is None:
            current_time = datetime.now()
            
        recency_score = self._calculate_recency(memory, current_time)
        frequency_score = self._calculate_frequency(memory)
        salience_score = self._calculate_salience(memory)
        
        return (self.recency_weight * recency_score + 
                self.frequency_weight * frequency_score + 
                self.salience_weight * salience_score)
    
    def _calculate_recency(self, memory: MemoryItem, current_time: datetime) -> float:
        """计算时间接近度分数"""
        time_diff = (current_time - memory.last_accessed).total_seconds()
        return max(0.0, 1.0 - (time_diff / (7 * 24 * 3600)))
    
    def _calculate_frequency(self, memory: MemoryItem) -> float:
        """计算访问频率分数"""
        return min(1.0, memory.access_count / 100)
    
    def _calculate_salience(self, memory: MemoryItem) -> float:
        """计算情感显著性分数"""
        return memory.importance


class MemoryRetrievalOptimizer:
    """记忆检索优化器，包含缓存和预取策略"""
    
    def __init__(self, cache_size: int = 100):
        """初始化优化器"""
        self.cache: OrderedDict = OrderedDict()
        self.cache_size = cache_size
        self.prefetch_enabled = True
        
    def get_cached(self, key: str) -> Optional[Any]:
        """从缓存获取结果"""
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set_cached(self, key: str, value: Any) -> None:
        """设置缓存"""
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.cache_size:
                self.cache.popitem(last=False)
        self.cache[key] = value
        
    def invalidate(self, key: str) -> None:
        """使缓存失效"""
        if key in self.cache:
            del self.cache[key]
            
    async def prefetch(self, keys: List[str], fetch_fn) -> None:
        """预取指定键的数据"""
        if not self.prefetch_enabled:
            return
            
        for key in keys:
            if key not in self.cache:
                try:
                    value = await fetch_fn(key)
                    self.set_cached(key, value)
                except Exception:
                    pass


class WorkingMemoryBuffer:
    """工作记忆缓冲区，管理活跃的工作记忆"""
    
    def __init__(self, capacity: int = 7):
        """初始化工作记忆缓冲区，容量默认为米勒定律7±2"""
        self.capacity = capacity
        self.buffer: deque = deque(maxlen=capacity)
        self.focus_index: int = 0
        
    def push(self, item: Any) -> None:
        """推入新项到缓冲区"""
        self.buffer.append(item)
        
    def get_focus(self) -> Optional[Any]:
        """获取当前焦点项"""
        if self.buffer:
            return self.buffer[self.focus_index]
        return None
        
    def shift_focus(self, direction: int = 1) -> None:
        """移动焦点方向"""
        if self.buffer:
            self.focus_index = (self.focus_index + direction) % len(self.buffer)
            
    def clear(self) -> None:
        """清空缓冲区"""
        self.buffer.clear()
        self.focus_index = 0
        
    def get_all(self) -> List[Any]:
        """获取所有项"""
        return list(self.buffer)
    
    def __len__(self) -> int:
        return len(self.buffer)
