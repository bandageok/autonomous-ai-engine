"""Context Manager - 上下文管理器
Context window management with priority-based selection and persistence
"""
import logging
import json
import threading
import datetime
import dataclasses
from typing import List, Dict, Generator, Optional, Callable, Union, Any
from collections import deque
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclasses.dataclass
class ContextConfig:
    """Configuration for ContextManager"""
    max_window_size: int = 100
    max_long_term_size: int = 1000
    summarizer: Callable[[str], str] = lambda x: x
    persistence_file: str = "context_persistence.json"
    summary_cache_size: int = 100
    priority_threshold: float = 0.5


@dataclasses.dataclass
class ContextItem:
    """Represents an individual context piece"""
    content: str
    timestamp: datetime.datetime
    priority: float
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)


class ContextManager:
    """Manages context windows with priority-based selection and persistence"""
    
    def __init__(self, config: ContextConfig = None):
        self.config = config or ContextConfig()
        self.lock = threading.Lock()
        self.short_term_context: deque = deque()
        self.long_term_context: List[ContextItem] = []
        self.summary_cache: Dict[str, str] = {}
        self._load_context()

    def _load_context(self):
        """Load persisted context from file"""
        try:
            with open(self.config.persistence_file, 'r') as f:
                data = json.load(f)
                self.short_term_context = deque(
                    ContextItem(**item) for item in data.get('short_term', [])
                )
                self.long_term_context = [
                    ContextItem(**item) for item in data.get('long_term', [])
                ]
                self._sync_contexts()
        except Exception as e:
            logger.error(f"Failed to load context: {str(e)}")

    def _save_context(self):
        """Persist context to file"""
        try:
            with open(self.config.persistence_file, 'w') as f:
                json.dump(
                    {
                        'short_term': [item.__dict__ for item in self.short_term_context],
                        'long_term': [item.__dict__ for item in self.long_term_context]
                    },
                    f
                )
        except Exception as e:
            logger.error(f"Failed to save context: {str(e)}")

    def _sync_contexts(self):
        """Synchronize context sizes with configuration limits"""
        with self.lock:
            # Sync short-term context
            while len(self.short_term_context) > self.config.max_window_size:
                self.short_term_context.popleft()
            
            # Sync long-term context
            while len(self.long_term_context) > self.config.max_long_term_size:
                self.long_term_context.pop(0)
            
            # Move oldest short-term items to long-term if needed
            while len(self.short_term_context) > self.config.max_window_size // 2:
                item = self.short_term_context.popleft()
                self.long_term_context.append(item)

    def add_context(self, content: str, priority: float = 0.0, metadata: Dict = None):
        """
        Add a new context item to the manager
        Args:
            content: The content of the context
            priority: Priority of the context (0.0-1.0)
            metadata: Additional metadata
        """
        if priority < 0 or priority > 1.0:
            raise ValueError("Priority must be between 0.0 and 1.0")
        
        item = ContextItem(
            content=content,
            timestamp=datetime.datetime.now(),
            priority=priority,
            metadata=metadata or {}
        )
        
        with self.lock:
            self.short_term_context.append(item)
            self._sync_contexts()
            self._save_context()
            logger.info(f"Added context: {content[:50]}... (priority: {priority})")

    def select_contexts(self, count: int = 10) -> List[ContextItem]:
        """
        Select top N context items based on priority
        Args:
            count: Number of contexts to select
        Returns:
            List of top context items
        """
        if count <= 0:
            return []
        
        with self.lock:
            # Combine short and long term contexts
            all_contexts = list(self.short_term_context) + self.long_term_context
            # Sort by priority descending
            sorted_contexts = sorted(
                all_contexts,
                key=lambda x: x.priority,
                reverse=True
            )
            
            # Apply priority threshold
            filtered = [
                ctx for ctx in sorted_contexts
                if ctx.priority >= self.config.priority_threshold
            ]
            
            return filtered[:count]

    def summarize_contexts(self, contexts: List[ContextItem]) -> Dict[str, str]:
        """
        Generate summaries for a list of contexts
        Args:
            contexts: List of ContextItem objects
        Returns:
            Dictionary mapping context IDs to summaries
        """
        result = {}
        for ctx in contexts:
            key = ctx.content[:10] + "-" + str(ctx.timestamp)
            if key in self.summary_cache:
                result[key] = self.summary_cache[key]
                continue
            
            summary = self.config.summarizer(ctx.content)
            self.summary_cache[key] = summary
            if len(self.summary_cache) > self.config.summary_cache_size:
                self.summary_cache.popitem(last=False)
            
            result[key] = summary
        
        return result

    def get_context_stream(self) -> Generator[ContextItem, None, None]:
        """Generator for lazy evaluation of context items"""
        with self.lock:
            yield from self.short_term_context
            yield from self.long_term_context

    def remove_context(self, content: str) -> bool:
        """Remove a context item by content"""
        with self.lock:
            for i, ctx in enumerate(self.short_term_context):
                if ctx.content == content:
                    self.short_term_context.pop(i)
                    self._save_context()
                    logger.info(f"Removed context: {content}")
                    return True
            
            for i, ctx in enumerate(self.long_term_context):
                if ctx.content == content:
                    self.long_term_context.pop(i)
                    self._save_context()
                    logger.info(f"Removed context: {content}")
                    return True
            
            logger.warning(f"Context not found: {content}")
            return False

    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about the current context state"""
        return {
            "short_term_count": len(self.short_term_context),
            "long_term_count": len(self.long_term_context),
            "total_contexts": len(self.short_term_context) + len(self.long_term_context),
            "summary_cache_size": len(self.summary_cache),
            "last_save_time": datetime.datetime.now().isoformat()
        }

    def __iter__(self):
        """Iterate over all context items"""
        return self.get_context_stream()

    def __len__(self):
        """Get total number of context items"""
        return len(self.short_term_context) + len(self.long_term_context)
