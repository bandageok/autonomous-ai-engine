"""RAG Chunker - 文档分块"""
from typing import List, Dict, Callable
import re

class ChunkStrategy:
    """分块策略基类"""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk(self, text: str) -> List[str]:
        raise NotImplementedError

class FixedSizeChunker(ChunkStrategy):
    """固定大小分块"""
    
    def chunk(self, text: str) -> List[str]:
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.overlap
            
        return [c for c in chunks if c.strip()]

class SentenceChunker(ChunkStrategy):
    """句子分块"""
    
    def chunk(self, text: str) -> List[str]:
        # 按句子分割
        sentences = re.split(r'[。！？!?]+\s*', text)
        
        chunks = []
        current = ""
        
        for sent in sentences:
            if len(current) + len(sent) <= self.chunk_size:
                current += sent + "。"
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = sent + "。"
                
        if current.strip():
            chunks.append(current.strip())
            
        return chunks

class ParagraphChunker(ChunkStrategy):
    """段落分块"""
    
    def chunk(self, text: str) -> List[str]:
        paragraphs = text.split("\n\n")
        
        chunks = []
        current = ""
        
        for para in paragraphs:
            if len(current) + len(para) <= self.chunk_size:
                current += para + "\n\n"
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = para + "\n\n"
                
        if current.strip():
            chunks.append(current.strip())
            
        return chunks

class SemanticChunker(ChunkStrategy):
    """语义分块"""
    
    def __init__(self, chunk_size: int = 500, embed_func: Callable = None):
        super().__init__(chunk_size, 0)
        self.embed_func = embed_func
        
    def chunk(self, text: str) -> List[str]:
        if not self.embed_func:
            return FixedSizeChunker(self.chunk_size).chunk(text)
            
        # 简化语义分块
        sentences = re.split(r'[。！？!?]+\s*', text)
        
        chunks = []
        current = ""
        
        for sent in sentences:
            if len(current) + len(sent) <= self.chunk_size:
                current += sent
            else:
                if current.strip():
                    chunks.append(current.strip())
                current = sent
                
        if current.strip():
            chunks.append(current.strip())
            
        return chunks
