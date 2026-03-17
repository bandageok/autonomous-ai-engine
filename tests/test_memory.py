"""Tests for Memory Module"""
import pytest
from agent.memory_system import MemoryStore, MemoryItem, MemoryType


class TestMemoryStore:
    """Test MemoryStore"""

    def test_store_creation(self):
        """Test store creation"""
        store = MemoryStore(max_size=100)
        assert store.max_size == 100
        assert len(store.store) == 0

    def test_add_memory(self):
        """Test adding memory"""
        store = MemoryStore()
        item = MemoryItem("test content", MemoryType.EPISODIC)
        store.add(item)
        assert len(store.store) == 1

    def test_memory_eviction(self):
        """Test memory eviction when full"""
        store = MemoryStore(max_size=2)
        item1 = MemoryItem("content 1", MemoryType.EPISODIC)
        item2 = MemoryItem("content 2", MemoryType.EPISODIC)
        item3 = MemoryItem("content 3", MemoryType.EPISODIC)

        store.add(item1)
        store.add(item2)
        store.add(item3)

        # Should have at most max_size items
        assert len(store.store) <= 2


class TestMemoryItem:
    """Test MemoryItem"""

    def test_item_creation(self):
        """Test memory item creation"""
        item = MemoryItem("test", MemoryType.SEMANTIC, importance=0.8)
        assert item.content == "test"
        assert item.type == MemoryType.SEMANTIC
        assert item.importance == 0.8

    def test_access(self):
        """Test memory access tracking"""
        item = MemoryItem("test", MemoryType.WORKING)
        initial_count = item.access_count

        item.access()
        assert item.access_count == initial_count + 1

    def test_to_dict(self):
        """Test serialization"""
        item = MemoryItem("test", MemoryType.EPISODIC)
        data = item.to_dict()
        assert data["content"] == "test"
        assert data["type"] == "episodic"
