"""Context Manager - 分层上下文管理
类似OpenViking的L0/L1/L2三层上下文结构
"""
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class ContextLevel(Enum):
    """上下文层级"""
    L0_HOT = "hot"      # 热数据 - 当前任务即时可用
    L1_WARM = "warm"   # 温数据 - 最近会话相关
    L2_COLD = "cold"   # 冷数据 - 长期记忆归档


@dataclass
class ContextItem:
    """上下文项"""
    id: str
    content: str
    level: ContextLevel
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    def touch(self):
        """更新访问时间"""
        self.access_count += 1
        self.last_accessed = datetime.now()


class ContextLayer:
    """上下文层"""
    
    def __init__(self, level: ContextLevel, max_items: int = 100):
        self.level = level
        self.max_items = max_items
        self.items: Dict[str, ContextItem] = {}
    
    def add(self, item: ContextItem):
        """添加项"""
        self.items[item.id] = item
        
        # 如果超过最大数量，移除最旧的
        if len(self.items) > self.max_items:
            oldest = min(self.items.values(), key=lambda x: x.last_accessed)
            del self.items[oldest.id]
    
    def get(self, item_id: str) -> Optional[ContextItem]:
        """获取项"""
        item = self.items.get(item_id)
        if item:
            item.touch()
        return item
    
    def remove(self, item_id: str) -> bool:
        """移除项"""
        if item_id in self.items:
            del self.items[item_id]
            return True
        return False
    
    def list_all(self) -> List[ContextItem]:
        """列出所有项"""
        return list(self.items.values())
    
    def clear(self):
        """清空层"""
        self.items.clear()
    
    def size(self) -> int:
        """大小"""
        return len(self.items)


class ContextManager:
    """分层上下文管理器"""
    
    def __init__(self, 
                 l0_capacity: int = 50,
                 l1_capacity: int = 200,
                 l2_capacity: int = 1000):
        self.layers = {
            ContextLevel.L0_HOT: ContextLayer(ContextLevel.L0_HOT, l0_capacity),
            ContextLevel.L1_WARM: ContextLayer(ContextLevel.L1_WARM, l1_capacity),
            ContextLevel.L2_COLD: ContextLayer(ContextLevel.L2_COLD, l2_capacity)
        }
        
        self.metadata: Dict[str, Any] = {}
        
    def add(self, content: str, level: ContextLevel, metadata: Dict = None) -> str:
        """添加上下文"""
        import hashlib
        
        item_id = hashlib.md5(content.encode()).hexdigest()[:16]
        
        item = ContextItem(
            id=item_id,
            content=content,
            level=level,
            metadata=metadata or {}
        )
        
        self.layers[level].add(item)
        
        return item_id
    
    def get(self, item_id: str) -> Optional[ContextItem]:
        """获取上下文 - 自动层级搜索"""
        # 先从热层开始查找
        for level in [ContextLevel.L0_HOT, ContextLevel.L1_WARM, ContextLevel.L2_COLD]:
            item = self.layers[level].get(item_id)
            if item:
                return item
        return None
    
    def search(self, query: str, top_k: int = 10) -> List[ContextItem]:
        """搜索上下文"""
        results = []
        query_lower = query.lower()
        
        # 搜索所有层
        for layer in self.layers.values():
            for item in layer.items.values():
                if query_lower in item.content.lower():
                    results.append(item)
        
        # 按访问频率排序
        results.sort(key=lambda x: (x.access_count, x.last_accessed), reverse=True)
        
        return results[:top_k]
    
    def get_all_for_context(self, max_tokens: int = 4000) -> str:
        """获取所有可用上下文 - 自动压缩"""
        context_parts = []
        remaining_tokens = max_tokens
        
        # 按优先级从热到冷
        for level in [ContextLevel.L0_HOT, ContextLevel.L1_WARM, ContextLevel.L2_COLD]:
            layer = self.layers[level]
            
            for item in layer.list_all():
                # 简单估算：1个token约4个字符
                estimated_tokens = len(item.content) // 4
                
                if estimated_tokens <= remaining_tokens:
                    context_parts.append(f"[{level.value}] {item.content}")
                    remaining_tokens -= estimated_tokens
                else:
                    break  # 满了
                    
            if remaining_tokens <= 0:
                break
        
        return "\n\n".join(context_parts)
    
    def promote(self, item_id: str) -> bool:
        """提升层级"""
        # 当前在哪个层
        current_level = None
        for level, layer in self.layers.items():
            if item_id in layer.items:
                current_level = level
                break
        
        if not current_level:
            return False
        
        # 提升到更高优先级
        item = self.layers[current_level].items[item_id]
        
        if current_level == ContextLevel.L2_COLD:
            new_level = ContextLevel.L1_WARM
        elif current_level == ContextLevel.L1_WARM:
            new_level = ContextLevel.L0_HOT
        else:
            return True  # 已经在最高层
        
        # 移动到新层
        self.layers[current_level].remove(item_id)
        item.level = new_level
        self.layers[new_level].add(item)
        
        return True
    
    def archive_to_l2(self, item_id: str) -> bool:
        """归档到L2"""
        for level in [ContextLevel.L0_HOT, ContextLevel.L1_WARM]:
            if item_id in self.layers[level].items:
                item = self.layers[level].items[item_id]
                self.layers[level].remove(item_id)
                item.level = ContextLevel.L2_COLD
                self.layers[ContextLevel.L2_COLD].add(item)
                return True
        return False
    
    def clear_level(self, level: ContextLevel):
        """清空指定层"""
        self.layers[level].clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "l0_hot": {
                "count": self.layers[ContextLevel.L0_HOT].size(),
                "max": self.layers[ContextLevel.L0_HOT].max_items
            },
            "l1_warm": {
                "count": self.layers[ContextLevel.L1_WARM].size(),
                "max": self.layers[ContextLevel.L1_WARM].max_items
            },
            "l2_cold": {
                "count": self.layers[ContextLevel.L2_COLD].size(),
                "max": self.layers[ContextLevel.L2_COLD].max_items
            }
        }
    
    def save_to_file(self, path: Path):
        """保存到文件"""
        data = {
            "layers": {},
            "metadata": self.metadata
        }
        
        for level, layer in self.layers.items():
            data["layers"][level.value] = [
                {
                    "id": item.id,
                    "content": item.content,
                    "metadata": item.metadata,
                    "created_at": item.created_at.isoformat(),
                    "access_count": item.access_count,
                    "last_accessed": item.last_accessed.isoformat()
                }
                for item in layer.items.values()
            ]
        
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_from_file(self, path: Path):
        """从文件加载"""
        if not path.exists():
            return
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.metadata = data.get("metadata", {})
        
        for level_str, items in data.get("layers", {}).items():
            level = ContextLevel(level_str)
            for item_data in items:
                item = ContextItem(
                    id=item_data["id"],
                    content=item_data["content"],
                    level=level,
                    metadata=item_data.get("metadata", {}),
                    created_at=datetime.fromisoformat(item_data["created_at"]),
                    access_count=item_data.get("access_count", 0),
                    last_accessed=datetime.fromisoformat(item_data["last_accessed"])
                )
                self.layers[level].add(item)


# 全局上下文管理器
_global_context = ContextManager()


def get_context_manager() -> ContextManager:
    """获取全局上下文管理器"""
    return _global_context
