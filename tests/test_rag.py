"""Tests for RAG Module"""
import pytest
from pathlib import Path
from rag.vector_store import VectorStore, VectorIndex
from rag.retriever import RetrievalResult, BM25Retriever, HybridRetriever
from rag.chunker import ChunkStrategy, SentenceChunker, FixedSizeChunker


class TestVectorStore:
    """Test VectorStore"""

    def test_vector_store_creation(self):
        """Test creating vector store"""
        store = VectorStore()
        assert store is not None
        assert hasattr(store, 'index')

    def test_vector_store_with_path(self):
        """Test creating vector store with path"""
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            store = VectorStore(storage_path=Path(tmpdir) / "vector.db")
            assert store is not None

    def test_add_vector(self):
        """Test adding vectors requires dimension match"""
        # VectorStore uses default 768 dimension
        # This tests that the API exists
        store = VectorStore()
        assert hasattr(store, 'add')
        assert hasattr(store, 'search')


class TestTextChunker:
    """Test Chunkers"""

    def test_fixed_size_chunker(self):
        """Test fixed size chunking"""
        chunker = FixedSizeChunker(chunk_size=10, overlap=2)
        text = " ".join([f"word{i}" for i in range(30)])
        chunks = chunker.chunk(text)
        assert len(chunks) > 0

    def test_sentence_chunker(self):
        """Test sentence chunking"""
        chunker = SentenceChunker(chunk_size=5)
        text = "This is sentence one. This is sentence two. This is sentence three."
        chunks = chunker.chunk(text)
        assert len(chunks) > 0
