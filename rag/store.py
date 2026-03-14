"""RAG Store - 向量存储"""
import numpy as np
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import json
import uuid

@dataclass
class VectorDoc:
    """向量文档"""
    id: str
    text: str
    embedding: np.ndarray
    metadata: Dict

class VectorStore:
    """向量存储"""
    
    def __init__(self, dimension: int = 768, metric: str = "cosine"):
        self.dimension = dimension
        self.metric = metric
        self.vectors: List[np.ndarray] = []
        self.documents: List[VectorDoc] = []
        self.metadata: List[Dict] = []
        
    def add(self, text: str, embedding: np.ndarray, metadata: Dict = None):
        """添加文档"""
        doc_id = str(uuid.uuid4())
        
        doc = VectorDoc(
            id=doc_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {}
        )
        
        self.vectors.append(embedding)
        self.documents.append(doc)
        self.metadata.append(metadata or {})
        
        return doc_id
        
    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[VectorDoc]:
        """搜索"""
        if not self.vectors:
            return []
            
        scores = []
        for i, vec in enumerate(self.vectors):
            if self.metric == "cosine":
                score = self._cosine_similarity(query_embedding, vec)
            else:
                score = -self._euclidean_distance(query_embedding, vec)
            scores.append((score, i))
            
        scores.sort(key=lambda x: x[0], reverse=True)
        
        return [self.documents[i] for _, i in scores[:top_k]]
        
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """余弦相似度"""
        dot = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        return float(dot / (norm_a * norm_b + 1e-8))
        
    def _euclidean_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """欧氏距离"""
        return float(np.linalg.norm(a - b))
        
    def save(self, path: str):
        """保存"""
        data = {
            "dimension": self.dimension,
            "metric": self.metric,
            "documents": [
                {
                    "id": d.id,
                    "text": d.text,
                    "embedding": d.embedding.tolist(),
                    "metadata": d.metadata
                }
                for d in self.documents
            ]
        }
        
        with open(path, "w") as f:
            json.dump(data, f)
            
    def load(self, path: str):
        """加载"""
        with open(path, "r") as f:
            data = json.load(f)
            
        self.dimension = data["dimension"]
        self.metric = data["metric"]
        
        for doc_data in data["documents"]:
            doc = VectorDoc(
                id=doc_data["id"],
                text=doc_data["text"],
                embedding=np.array(doc_data["embedding"]),
                metadata=doc_data["metadata"]
            )
            self.documents.append(doc)
            self.vectors.append(doc.embedding)
            self.metadata.append(doc.metadata)
