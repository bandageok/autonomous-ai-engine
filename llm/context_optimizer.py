
    """Context Optimizer - 上下文优化器"""
    from typing import Dict, List, Optional, Tuple
    import re
    from collections import Counter
    
    class ContextItem:
        """上下文项"""
        def __init__(self, text: str, importance: float = 0.5, token_count: int = 0):
            self.text = text
            self.importance = importance
            self.token_count = token_count or self.estimate_tokens(text)
            
        def estimate_tokens(self, text: str) -> int:
            """估算token数量(中文约1.5字符/token,英文约4字符/token)"""
            chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
            english = len(text) - chinese
            return int(chinese / 1.5 + english / 4)
            
    class RelevanceScorer:
        """相关性评分器"""
        
        def __init__(self):
            self.keywords_weight = 2.0
            self.recency_weight = 1.5
            self.length_weight = 0.5
            
        def score(self, item: ContextItem, query: str) -> float:
            """计算相关性分数"""
            score = item.importance
            
            # 关键词匹配
            query_keywords = set(query.lower().split())
            item_keywords = set(item.text.lower().split())
            overlap = len(query_keywords & item_keywords)
            score += overlap * self.keywords_weight * 0.1
            
            # 长度惩罚
            if item.token_count > 1000:
                score *= self.length_weight
                
            return score
            
    class ContextOptimizer:
        """上下文优化器"""
        
        def __init__(self, max_tokens: int = 8000):
            self.max_tokens = max_tokens
            self.scorer = RelevanceScorer()
            self.items: List[ContextItem] = []
            
        def add_context(self, text: str, importance: float = 0.5):
            """添加上下文"""
            item = ContextItem(text, importance)
            self.items.append(item)
            
        def optimize(self, query: str = "") -> str:
            """优化上下文"""
            if not query:
                # 无查询,按重要性排序
                sorted_items = sorted(
                    self.items, 
                    key=lambda x: x.importance, 
                    reverse=True
                )
            else:
                # 按相关性排序
                sorted_items = sorted(
                    self.items,
                    key=lambda x: self.scorer.score(x, query),
                    reverse=True
                )
                
            # 裁剪到最大token数
            total_tokens = 0
            result = []
            
            for item in sorted_items:
                if total_tokens + item.token_count <= self.max_tokens:
                    result.append(item.text)
                    total_tokens += item.token_count
                else:
                    # 尝试裁剪当前项
                    remaining = self.max_tokens - total_tokens
                    if remaining > 100:
                        truncated = item.text[:int(remaining * 4)]
                        result.append(truncated)
                    break
                    
            return "\n\n".join(result)
            
        def compress(self, text: str, target_tokens: int) -> str:
            """压缩文本"""
            item = ContextItem(text)
            
            if item.token_count <= target_tokens:
                return text
                
            # 简单压缩:提取关键句子
            sentences = re.split(r'[。！？\n]', text)
            result = []
            total = 0
            
            for sent in sentences:
                sent_tokens = ContextItem(sent).token_count
                if total + sent_tokens <= target_tokens:
                    result.append(sent)
                    total += sent_tokens
                else:
                    break
                    
            return "。".join(result) + "。"
            
        def get_stats(self) -> Dict:
            """获取统计信息"""
            total = sum(i.token_count for i in self.items)
            return {
                "total_items": len(self.items),
                "total_tokens": total,
                "max_tokens": self.max_tokens,
                "utilization": total / self.max_tokens if self.max_tokens > 0 else 0
            }


    """Context Optimizer - 上下文优化器"""
    from typing import Dict, List, Optional, Tuple
    import re
    from collections import Counter
    
    class ContextItem:
        """上下文项"""
        def __init__(self, text: str, importance: float = 0.5, token_count: int = 0):
            self.text = text
            self.importance = importance
            self.token_count = token_count or self.estimate_tokens(text)
            
        def estimate_tokens(self, text: str) -> int:
            """估算token数量(中文约1.5字符/token,英文约4字符/token)"""
            chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
            english = len(text) - chinese
            return int(chinese / 1.5 + english / 4)
            
    class RelevanceScorer:
        """相关性评分器"""
        
        def __init__(self):
            self.keywords_weight = 2.0
            self.recency_weight = 1.5
            self.length_weight = 0.5
            
        def score(self, item: ContextItem, query: str) -> float:
            """计算相关性分数"""
            score = item.importance
            
            # 关键词匹配
            query_keywords = set(query.lower().split())
            item_keywords = set(item.text.lower().split())
            overlap = len(query_keywords & item_keywords)
            score += overlap * self.keywords_weight * 0.1
            
            # 长度惩罚
            if item.token_count > 1000:
                score *= self.length_weight
                
            return score
            
    class ContextOptimizer:
        """上下文优化器"""
        
        def __init__(self, max_tokens: int = 8000):
            self.max_tokens = max_tokens
            self.scorer = RelevanceScorer()
            self.items: List[ContextItem] = []
            
        def add_context(self, text: str, importance: float = 0.5):
            """添加上下文"""
            item = ContextItem(text, importance)
            self.items.append(item)
            
        def optimize(self, query: str = "") -> str:
            """优化上下文"""
            if not query:
                # 无查询,按重要性排序
                sorted_items = sorted(
                    self.items, 
                    key=lambda x: x.importance, 
                    reverse=True
                )
            else:
                # 按相关性排序
                sorted_items = sorted(
                    self.items,
                    key=lambda x: self.scorer.score(x, query),
                    reverse=True
                )
                
            # 裁剪到最大token数
            total_tokens = 0
            result = []
            
            for item in sorted_items:
                if total_tokens + item.token_count <= self.max_tokens:
                    result.append(item.text)
                    total_tokens += item.token_count
                else:
                    # 尝试裁剪当前项
                    remaining = self.max_tokens - total_tokens
                    if remaining > 100:
                        truncated = item.text[:int(remaining * 4)]
                        result.append(truncated)
                    break
                    
            return "\n\n".join(result)
            
        def compress(self, text: str, target_tokens: int) -> str:
            """压缩文本"""
            item = ContextItem(text)
            
            if item.token_count <= target_tokens:
                return text
                
            # 简单压缩:提取关键句子
            sentences = re.split(r'[。！？\n]', text)
            result = []
            total = 0
            
            for sent in sentences:
                sent_tokens = ContextItem(sent).token_count
                if total + sent_tokens <= target_tokens:
                    result.append(sent)
                    total += sent_tokens
                else:
                    break
                    
            return "。".join(result) + "。"
            
        def get_stats(self) -> Dict:
            """获取统计信息"""
            total = sum(i.token_count for i in self.items)
            return {
                "total_items": len(self.items),
                "total_tokens": total,
                "max_tokens": self.max_tokens,
                "utilization": total / self.max_tokens if self.max_tokens > 0 else 0
            }
