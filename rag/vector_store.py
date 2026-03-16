"""Vector Store - 向量存储"""
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
import json
import hashlib
from dataclasses import dataclass, asdict
import pickle


@dataclass
class VectorEntry:
    """向量条目"""
    id: str
    vector: np.ndarray
    text: str
    metadata: Dict[str, Any]
    score: float = 0.0


class VectorIndex:
    """向量索引"""
    
    def __init__(self, dimension: int = 768, metric: str = "cosine"):
        self.dimension = dimension
        self.metric = metric
        self.vectors: List[np.ndarray] = []
        self.entries: List[VectorEntry] = []
        self.metadata: Dict[str, Any] = {}
        
    def add(self, entry: VectorEntry):
        """添加向量"""
        if len(entry.vector) != self.dimension:
            raise ValueError(f"Dimension mismatch: expected {self.dimension}, got {len(entry.vector)}")
            
        self.vectors.append(entry.vector)
        self.entries.append(entry)
        
    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[VectorEntry]:
        """搜索"""
        if not self.vectors:
            return []
            
        scores = []
        
        for i, vec in enumerate(self.vectors):
            if self.metric == "cosine":
                score = self._cosine_similarity(query_vector, vec)
            elif self.metric == "euclidean":
                score = -self._euclidean_distance(query_vector, vec)
            else:
                score = 0
                
            entry = self.entries[i]
            entry.score = score
            scores.append((score, entry))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        
        return [entry for _, entry in scores[:top_k]]
        
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度"""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return float(dot / (norm_a * norm_b))
        
    def _euclidean_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """欧氏距离"""
        return float(np.linalg.norm(a - b))
        
    def save(self, path: Path):
        """保存索引"""
        data = {
            "dimension": self.dimension,
            "metric": self.metric,
            "entries": [
                {
                    "id": e.id,
                    "vector": e.vector.tolist(),
                    "text": e.text,
                    "metadata": e.metadata
                }
                for e in self.entries
            ],
            "metadata": self.metadata
        }
        
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
            
    @classmethod
    def load(cls, path: Path) -> "VectorIndex":
        """加载索引"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        index = cls(dimension=data["dimension"], metric=data["metric"])
        
        for e in data["entries"]:
            entry = VectorEntry(
                id=e["id"],
                vector=np.array(e["vector"]),
                text=e["text"],
                metadata=e["metadata"]
            )
            index.add(entry)
            
        index.metadata = data.get("metadata", {})
        
        return index


class VectorStore:
    """向量存储"""
    
    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path
        self.index = VectorIndex()
        self.id_to_entry: Dict[str, VectorEntry] = {}
        
        if storage_path and storage_path.exists():
            self.index = VectorIndex.load(storage_path)
            self.id_to_entry = {e.id: e for e in self.index.entries}
            
    def add(self, text: str, vector: np.ndarray, metadata: Optional[Dict] = None):
        """添加向量"""
        entry_id = hashlib.md5(text.encode()).hexdigest()[:16]
        
        entry = VectorEntry(
            id=entry_id,
            vector=vector,
            text=text,
            metadata=metadata or {}
        )
        
        self.index.add(entry)
        self.id_to_entry[entry_id] = entry
        
        if self.storage_path:
            self.index.save(self.storage_path)
            
    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[VectorEntry]:
        """搜索"""
        return self.index.search(query_vector, top_k)
        
    def search_by_text(self, query_text: str, embed_func, top_k: int = 10) -> List[VectorEntry]:
        """通过文本搜索"""
        query_vector = embed_func(query_text)
        return self.search(query_vector, top_k)
        
    def get(self, entry_id: str) -> Optional[VectorEntry]:
        """获取条目"""
        return self.id_to_entry.get(entry_id)
        
    def delete(self, entry_id: str):
        """删除条目"""
        if entry_id in self.id_to_entry:
            entry = self.id_to_entry[entry_id]
            idx = self.index.entries.index(entry)
            
            del self.index.vectors[idx]
            del self.index.entries[idx]
            del self.id_to_entry[entry_id]
            
            if self.storage_path:
                self.index.save(self.storage_path)
                
    def count(self) -> int:
        """计数"""
        return len(self.index.entries)
