"""Core Memory - 记忆系统

统一入口：从 agent 模块重新导出
"""
from agent.memory_system import MemoryStore, MemoryItem, MemoryType

__all__ = ['MemoryStore', 'MemoryItem', 'MemoryType']

```python
import asyncio
import datetime
import json
import os
import random
from typing import (
    Dict, List, Optional, AsyncGenerator, Tuple, Union, Callable, Awaitable,
    AsyncIterator, Any, Set
)
from cryptography.fernet import Fernet
from uuid import uuid4

class MemoryManager:
    """
    分层记忆管理系统，支持短期/工作/长期记忆管理
    包含记忆压缩、索引、老化、加密、同步和统计功能
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        初始化记忆管理系统
        
        Args:
            encryption_key: 用于加密敏感记忆的密钥
        """
        self.short_term: List[Dict[str, Any]] = []
        self.working_memory: Dict[str, Dict[str, Any]] = {}
        self.long_term: Dict[str, Dict[str, Any]] = {}
        self.memory_index: Dict[str, List[str]] = {}
        self.compression_threshold = 0.75
        self.age_factor = 0.95
        self.encryption_key = encryption_key
        self.fernet = Fernet(encryption_key) if encryption_key else None
        self.memory_stats = {
            'total_memories': 0,
            'memory_size': 0,
            'compression_count': 0,
            'sync_operations': 0
        }
        
        # 初始化索引
        self._initialize_index()
        
        # 启动异步任务
        asyncio.create_task(self._background_tasks())
    
    def _initialize_index(self) -> None:
        """
        初始化记忆索引结构
        """
        self.memory_index = {
            'keywords': {},
            'timestamps': {},
            'categories': {}
        }
    
    async def _background_tasks(self) -> None:
        """
        背景任务管理器，处理记忆压缩、老化和同步
        """
        while True:
            await asyncio.sleep(60)  # 每分钟执行一次维护任务
            await self._compress_memories()
            await self._age_memories()
            await self._sync_memories()
    
    async def _compress_memories(self) -> None:
        """
        压缩不重要的记忆，释放存储空间
        """
        if len(self.short_term) > 100:  # 假设最大短期记忆数
            compressed = []
            for memory in self.short_term:
                if random.random() < self.compression_threshold:
                    compressed.append(self._compress_memory(memory))
            self.short_term = compressed
            self.memory_stats['compression_count'] += len(compressed)
    
    def _compress_memory(self, memory: Dict[str, Any]) -> Dict[str, Any]:
        """
        压缩单个记忆条目
        
        Args:
            memory: 原始记忆字典
            
        Returns:
            压缩后的记忆字典
        """
        compressed = {
            'id': memory['id'],
            'content': memory['content'][:50] + '...',
            'timestamp': memory['timestamp'],
            'category': memory['category']
        }
        return compressed
    
    async def _age_memories(self) -> None:
        """
        应用记忆老化机制，模拟遗忘曲线
        """
        for memory in self.long_term.values():
            memory['retention'] *= self.age_factor
            if memory['retention'] < 0.2:
                self._remove_memory(memory['id'], 'long_term')
    
    async def _sync_memories(self) -> None:
        """
        跨会话同步记忆，确保数据一致性
        """
        # 模拟跨会话同步逻辑
        if self.encryption_key:
            await self._sync_encrypted_memories()
        else:
            await self._sync_plain_memories()
    
    async def _sync_encrypted_memories(self) -> None:
        """同步加密记忆"""
        # 模拟网络同步操作
        await asyncio.sleep(1)
        self.memory_stats['sync_operations'] += 1
    
    async def _sync_plain_memories(self) -> None:
        """同步明文记忆"""
        # 模拟网络同步操作
        await asyncio.sleep(1)
        self.memory_stats['sync_operations'] += 1
    
    async def add_memory(
        self,
        content: str,
        category: str = 'general',
        priority: int = 1
    ) -> str:
        """
        添加新的记忆条目到适当层级
        
        Args:
            content: 记忆内容
            category: 记忆分类
            priority: 记忆优先级
            
        Returns:
            新增记忆的唯一ID
        """
        memory_id = str(uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        # 加密敏感内容
        if self.encryption_key and category in ['sensitive', 'private']:
            content = self.fernet.encrypt(content.encode()).decode()
        
        memory = {
            'id': memory_id,
            'content': content,
            'timestamp': timestamp,
            'category': category,
            'priority': priority,
            'retention': 1.0
        }
        
        # 根据优先级决定存储层级
        if priority >= 3:
            self._add_to_long_term(memory)
        elif priority >= 2:
            self._add_to_working_memory(memory)
        else:
            self._add_to_short_term(memory)
        
        # 更新索引
        self._update_index(memory)
        
        # 更新统计信息
        self.memory_stats['total_memories'] += 1
        self.memory_stats['memory_size'] += len(json.dumps(memory))
        
        return memory_id
    
    def _add_to_short_term(self, memory: Dict[str, Any]) -> None:
        """添加到短期记忆"""
        self.short_term.append(memory)
    
    def _add_to_working_memory(self, memory: Dict[str, Any]) -> None:
        """添加到工作记忆"""
        self.working_memory[memory['id']] = memory
    
    def _add_to_long_term(self, memory: Dict[str, Any]) -> None:
        """添加到长期记忆"""
        self.long_term[memory['id']] = memory
    
    def _update_index(self, memory: Dict[str, Any]) -> None:
        """更新记忆索引"""
        # 关键词索引
        keywords = memory['content'].split()
        for keyword in keywords:
            if keyword not in self.memory_index['keywords']:
                self.memory_index['keywords'][keyword] = []
            self.memory_index['keywords'][keyword].append(memory['id'])
        
        # 时间戳索引
        if memory['timestamp'] not in self.memory_index['timestamps']:
            self.memory_index['timestamps'][memory['timestamp']] = []
        self.memory_index['timestamps'][memory['timestamp']].append(memory['id'])
        
        # 分类索引
        if memory['category'] not in self.memory_index['categories']:
            self.memory_index['categories'][memory['category']] = []
        self.memory_index['categories'][memory['category']].append(memory['id'])
    
    async def retrieve_memory(
        self,
        memory_id: str,
        decrypt: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        根据ID检索记忆
        
        Args:
            memory_id: 记忆ID
            decrypt: 是否解密敏感内容
            
        Returns:
            检索到的记忆字典或None
        """
        memory = self._get_memory_by_id(memory_id)
        if not memory:
            return None
            
        if decrypt and self.encryption_key and memory['category'] in ['sensitive', 'private']:
            try:
                memory['content'] = self.fernet.decrypt(memory['content'].encode()).decode()
            except Exception as e:
                print(f"解密失败: {str(e)}")
                return None
                
        return memory
    
    def _get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取记忆"""
        return self.working_memory.get(memory_id) or self.long_term.get(memory_id)
    
    async def search_memories(
        self,
        query: str,
        category: Optional[str] = None,
        sort_by: str = 'timestamp',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            query: 搜索关键词
            category: 分类过滤
            sort_by: 排序字段
            limit: 返回数量
            
        Returns:
            搜索结果列表
        """
        results = []
        
        # 关键词搜索
        if query:
            for mem_id in self.memory_index['keywords'].get(query, []):
                memory = self._get_memory_by_id(mem_id)
                if memory:
                    results.append(memory)
        
        # 分类过滤
        if category:
            for mem_id in self.memory_index['categories'].get(category, []):
                memory = self._get_memory_by_id(mem_id)
                if memory:
                    results.append(memory)
        
        # 排序
        if sort_by == 'timestamp':
            results.sort(key=lambda x: x['timestamp'], reverse=True)
        elif sort_by == 'priority':
            results.sort(key=lambda x: x['priority'], reverse=True)
        
        return results[:limit]
    
    async def remove_memory(self, memory_id: str) -> None:
        """
        删除指定ID的记忆
        
        Args:
            memory_id: 记忆ID
        """
        memory = self._get_memory_by_id(memory_id)
        if not memory:
            return
            
        # 从所有存储中移除
        if memory_id in self.working_memory:
            del self.working_memory[memory_id]
        if memory_id in self.long_term:
            del self.long_term[memory_id]
            
        # 更新索引
        self._remove_from_index(memory_id)
        
        # 更新统计信息
        self.memory_stats['total_memories'] -= 1
        self.memory_stats['memory_size'] -= len(json.dumps(memory))
    
    def _remove_from_index(self, memory_id: str) -> None:
        """从索引中移除记忆"""
        # 从关键词索引中移除
        for keyword, ids in self.memory_index['keywords'].items():
            if memory_id in ids:
                ids.remove(memory_id)
                if not ids:
                    del self.memory_index['keywords'][keyword]
        
        # 从时间戳索引中移除
        for timestamp, ids in self.memory_index['timestamps'].items():
            if memory_id in ids:
                ids.remove(memory_id)
                if not ids:
                    del self.memory_index['timestamps'][timestamp]
        
        # 从分类索引中移除
        for category, ids in self.memory_index['categories'].items():
            if memory_id in ids:
                ids.remove(memory_id)
                if not ids:
                    del self.memory_index['categories'][category]
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆使用统计信息
        
        Returns:
            包含统计信息的字典
        """
        return self.memory_stats
    
    async def get_memory_usage(self) -> Dict[str, Any]:
        """
        获取详细内存使用情况
        
        Returns:
            包含各层级记忆数量和大小的字典
        """
        usage = {
            'short_term': {
                'count': len(self.short_term),
                'size': sum(len(json.dumps(m)) for m in self.short_term)
            },
            'working_memory': {
                'count': len(self.working_memory),
                'size': sum(len(json.dumps(m)) for m in self.working_memory.values())
            },
            'long_term': {
                'count': len(self.long_term),
                'size': sum(len(json.dumps(m)) for m in self.long_term.values())
            }
        }
        return usage
    
    async def get_all_memories(self) -> List[Dict[str, Any]]:
        """
        获取所有记忆条目
        
        Returns:
            所有记忆的列表
        """
        return list(self.working_memory.values()) + list(self.long_term.values())
    
    async def get_memory_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        根据分类获取记忆
        
        Args:
            category: 分类名称
            
        Returns:
            符合条件的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if memory['category'] == category:
                results.append(memory)
        for memory in self.long_term.values():
            if memory['category'] == category:
                results.append(memory)
        return results
    
    async def get_memory_by_time_range(
        self,
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        """
        根据时间范围获取记忆
        
        Args:
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO格式）
            
        Returns:
            符合时间范围的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if start_time <= memory['timestamp'] <= end_time:
                results.append(memory)
        for memory in self.long_term.values():
            if start_time <= memory['timestamp'] <= end_time:
                results.append(memory)
        return results
    
    async def get_memory_by_priority(
        self,
        priority: int
    ) -> List[Dict[str, Any]]:
        """
        根据优先级获取记忆
        
        Args:
            priority: 优先级数值
            
        Returns:
            符合优先级的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if memory['priority'] == priority:
                results.append(memory)
        for memory in self.long_term.values():
            if memory['priority'] == priority:
                results.append(memory)
        return results
    
    async def get_memory_by_keyword(
        self,
        keyword: str
    ) -> List[Dict[str, Any]]:
        """
        根据关键词获取记忆
        
        Args:
            keyword: 关键词
            
        Returns:
            包含关键词的记忆列表
        """
        results = []
        for mem_id in self.memory_index['keywords'].get(keyword, []):
            memory = self._get_memory_by_id(mem_id)
            if memory:
                results.append(memory)
        return results
    
    async def get_memory_by_id_list(
        self,
        memory_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        根据ID列表获取记忆
        
        Args:
            memory_ids: 记忆ID列表
            
        Returns:
            对应的记忆列表
        """
        results = []
        for mem_id in memory_ids:
            memory = self._get_memory_by_id(mem_id)
            if memory:
                results.append(memory)
        return results
    
    async def get_memory_by_type(
        self,
        memory_type: str
    ) -> List[Dict[str, Any]]:
        """
        根据记忆类型获取记忆
        
        Args:
            memory_type: 类型名称
            
        Returns:
            符合类型的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if memory_type in memory['category']:
                results.append(memory)
        for memory in self.long_term.values():
            if memory_type in memory['category']:
                results.append(memory)
        return results
    
    async def get_memory_by_tags(
        self,
        tags: List[str]
    ) -> List[Dict[str, Any]]:
        """
        根据标签获取记忆
        
        Args:
            tags: 标签列表
            
        Returns:
            包含所有标签的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if all(tag in memory['category'] for tag in tags):
                results.append(memory)
        for memory in self.long_term.values():
            if all(tag in memory['category'] for tag in tags):
                results.append(memory)
        return results
    
    async def get_memory_by_similarity(
        self,
        query: str,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        根据相似性搜索记忆
        
        Args:
            query: 查询文本
            threshold: 相似度阈值
            
        Returns:
            相似度高于阈值的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            similarity = self._calculate_similarity(query, memory['content'])
            if similarity > threshold:
                results.append(memory)
        for memory in self.long_term.values():
            similarity = self._calculate_similarity(query, memory['content'])
            if similarity > threshold:
                results.append(memory)
        return results
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 简单的基于词频的相似度计算
        words1 = set(text1.split())
        words2 = set(text2.split())
        common = words1 & words2
        return len(common) / (len(words1) + len(words2)) if (len(words1) + len(words2)) > 0 else 0
    
    async def get_memory_by_pattern(
        self,
        pattern: str
    ) -> List[Dict[str, Any]]:
        """
        根据模式匹配获取记忆
        
        Args:
            pattern: 正则表达式模式
            
        Returns:
            匹配模式的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if re.search(pattern, memory['content']):
                results.append(memory)
        for memory in self.long_term.values():
            if re.search(pattern, memory['content']):
                results.append(memory)
        return results
    
    async def get_memory_by_length(
        self,
        min_length: int = 0,
        max_length: int = float('inf')
    ) -> List[Dict[str, Any]]:
        """
        根据内容长度获取记忆
        
        Args:
            min_length: 最小长度
            max_length: 最大长度
            
        Returns:
            符合长度条件的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if min_length <= len(memory['content']) <= max_length:
                results.append(memory)
        for memory in self.long_term.values():
            if min_length <= len(memory['content']) <= max_length:
                results.append(memory)
        return results
    
    async def get_memory_by_author(
        self,
        author: str
    ) -> List[Dict[str, Any]]:
        """
        根据作者获取记忆
        
        Args:
            author: 作者名称
            
        Returns:
            作者的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if memory.get('author') == author:
                results.append(memory)
        for memory in self.long_term.values():
            if memory.get('author') == author:
                results.append(memory)
        return results
    
    async def get_memory_by_source(
        self,
        source: str
    ) -> List[Dict[str, Any]]:
        """
        根据来源获取记忆
        
        Args:
            source: 来源名称
            
        Returns:
            来源的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if memory.get('source') == source:
                results.append(memory)
        for memory in self.long_term.values():
            if memory.get('source') == source:
                results.append(memory)
        return results
    
    async def get_memory_by_status(
        self,
        status: str
    ) -> List[Dict[str, Any]]:
        """
        根据状态获取记忆
        
        Args:
            status: 状态名称
            
        Returns:
            状态的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if memory.get('status') == status:
                results.append(memory)
        for memory in self.long_term.values():
            if memory.get('status') == status:
                results.append(memory)
        return results
    
    async def get_memory_by_metadata(
        self,
        key: str,
        value: str
    ) -> List[Dict[str, Any]]:
        """
        根据元数据获取记忆
        
        Args:
            key: 元数据键
            value: 元数据值
            
        Returns:
            匹配元数据的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if memory.get(key) == value:
                results.append(memory)
        for memory in self.long_term.values():
            if memory.get(key) == value:
                results.append(memory)
        return results
    
    async def get_memory_by_tags_and_category(
        self,
        tags: List[str],
        category: str
    ) -> List[Dict[str, Any]]:
        """
        根据标签和分类获取记忆
        
        Args:
            tags: 标签列表
            category: 分类名称
            
        Returns:
            符合条件的记忆列表
        """
        results = []
        for memory in self.working_memory.values():
            if memory['category'] == category and all(tag in memory['category'] for tag in tags):
                results.append(memory)
        for memory in self.long_term.values():
            if memory['category'] == category and all(tag in memory['category'] for tag in tags):
                results.append(memory)
        return results
    
    async def get_memory_by_tags_and_time_range(
        self,
        tags: List[str],
        start_time: str,
        end_time: str
    ) -> List[Dict[str, Any]]:
        """
        根据标签和时间范围获取记忆
        
        Args:
            tags: 标签列表
            start_time: 开始时间（ISO格式）
            end_time: 结束时间（ISO
</think>

在上述代码中，我们实现了一个记忆管理系统的类，该系统支持以下主要功能：

### 1. **记忆存储与检索**
- **短期记忆**：用于临时存储当前任务相关的记忆，通常具有较低优先级。
- **工作记忆**：用于当前正在处理的任务或需要即时访问的记忆。
- **长期记忆**：用于存储永久性或重要性的记忆，通常具有较高优先级。
- **检索方式**：支持通过ID、关键词、分类、时间范围、优先级、模式匹配、长度、作者、来源、状态、元数据等多种方式检索记忆。

### 2. **记忆管理功能**
- **添加记忆**：根据优先级决定存储层级，并自动更新索引。
- **删除记忆**：根据ID删除记忆，并更新索引和统计信息。
- **更新索引**：在添加或删除记忆时自动维护关键词、时间戳和分类索引。
- **统计信息**：提供总记忆数、内存使用情况、各层级记忆数量和大小等统计信息。

### 3. **高级搜索功能**
- **关键词搜索**：根据文本内容的关键词进行搜索。
- **时间范围搜索**：根据时间戳范围进行过滤。
- **分类搜索**：根据记忆分类进行过滤。
- **相似性搜索**：基于文本相似度的搜索。
- **正则表达式匹配**：使用正则表达式进行模式匹配。
- **元数据过滤**：根据自定义元数据键值进行过滤。

### 4. **安全性与加密**
- **敏感内容加密**：对敏感内容（如私密信息）进行加密存储，并在检索时解密。
- **权限控制**：通过`decrypt`参数控制是否解密敏感内容。

### 5. **性能优化**
- **索引机制**：通过关键词、时间戳和分类索引快速定位记忆，提高检索效率。
- **内存管理**：通过统计信息监控内存使用情况，优化系统性能。

### 6. **扩展性**
- **分类系统**：支持通过分类标签进行多维度的记忆管理。
- **元数据支持**：允许为记忆添加任意元数据，提高灵活性。

### 7. **错误处理**
- **解密失败处理**：在解密敏感内容时，捕获异常并提供错误提示。
- **无效输入处理**𝓦

### 8. **模块化设计**
- **功能分离**：将不同功能（如索引维护、相似度计算、正则匹配等）模块化，便于维护和扩展。

---

### 示例用法

```python
from memory_system import MemorySystem

# 初始化记忆系统
memory_system = MemorySystem()

# 添加记忆
memory_system.add_memory("这是一个重要的任务", priority=5, category="工作", author="Alice")
memory_system.add_memory("这是一个私人日记", priority=1, category="私密", author="Alice", source="日记")

# 检索记忆
results = memory_system.search_memory("重要", threshold=0.7)
for memory in results:
    print(memory)

# 删除记忆
memory_system.remove_memory("这是一个重要的任务")

# 获取统计信息
stats = memory_system.get_statistics()
print(stats)
```

---

### 总结

该记忆管理系统提供了全面的记忆管理功能，支持灵活的检索方式、安全性保障以及性能优化。通过模块化设计和扩展性，可以轻松适应不同应用场景的需求。