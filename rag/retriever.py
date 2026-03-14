
    """Retriever - 检索器"""
    from typing import List, Dict, Optional, Any, Callable
    import numpy as np
    from collections import defaultdict
    
    class RetrievalResult:
        """检索结果"""
        def __init__(self, text: str, score: float, metadata: Dict):
            self.text = text
            self.score = score
            self.metadata = metadata
            
        def __repr__(self):
            return f"RetrievedResult(score={self.score:.3f}, text={self.text[:50]}...)"
            
    class BM25Retriever:
        """BM25检索器"""
        
        def __init__(self, k1: float = 1.5, b: float = 0.75):
            self.k1 = k1
            self.b = b
            self.documents: List[str] = []
            self.doc_lengths: List[int] = []
            self.avg_doc_length: float = 0
            self.doc_freq: Dict[str, int] = defaultdict(int)
            self.tokenized_docs: List[List[str]] = []
            
        def add_document(self, doc: str, metadata: Optional[Dict] = None):
            """添加文档"""
            tokens = self._tokenize(doc)
            
            self.documents.append(doc)
            self.doc_lengths.append(len(tokens))
            self.tokenized_docs.append(tokens)
            
            # 更新文档频率
            for token in set(tokens):
                self.doc_freq[token] += 1
                
            # 更新平均长度
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
            
        def _tokenize(self, text: str) -> List[str]:
            """分词"""
            import re
            text = text.lower()
            tokens = re.findall(r'\w+', text)
            return tokens
            
        def search(self, query: str, top_k: int = 10) -> List[RetrievalResult]:
            """搜索"""
            query_tokens = self._tokenize(query)
            n = len(self.documents)
            
            scores = []
            
            for i, doc_tokens in enumerate(self.tokenized_docs):
                score = 0
                doc_length = self.doc_lengths[i]
                
                for token in query_tokens:
                    if token not in doc_tokens:
                        continue
                        
                    # 计算BM25分数
                    tf = doc_tokens.count(token)
                    df = self.doc_freq[token]
                    
                    idf = np.log((n - df + 0.5) / (df + 0.5) + 1)
                    
                    numerator = tf * (self.k1 + 1)
                    denominator = tf + self.k1 * (1 - self.b + self.b * doc_length / self.avg_doc_length)
                    
                    score += idf * numerator / denominator
                    
                scores.append((score, i))
                
            # 排序
            scores.sort(key=lambda x: x[0], reverse=True)
            
            results = []
            for score, idx in scores[:top_k]:
                results.append(RetrievalResult(
                    text=self.documents[idx],
                    score=score,
                    metadata={}
                ))
                
            return results
            
    class HybridRetriever:
        """混合检索器"""
        
        def __init__(self, vector_weight: float = 0.5, keyword_weight: float = 0.5):
            self.vector_weight = vector_weight
            self.keyword_weight = keyword_weight
            self.vector_results: List[RetrievalResult] = []
            self.keyword_results: List[RetrievalResult] = []
            
        def search(self, query: str, vector_func: Callable, 
                   documents: List[str], top_k: int = 10) -> List[RetrievalResult]:
            """混合搜索"""
            # 向量检索
            query_vector = vector_func(query)
            
            # 这里简化处理,实际应该调用VectorStore
            vector_results = []
            
            # 关键词检索
            bm25 = BM25Retriever()
            for doc in documents:
                bm25.add_document(doc)
                
            keyword_results = bm25.search(query, top_k)
            
            # 合并结果
            all_docs = {}
            
            for r in vector_results:
                all_docs[r.text] = all_docs.get(r.text, [0, 0])
                all_docs[r.text][0] = r.score * self.vector_weight
                
            for r in keyword_results:
                all_docs[r.text] = all_docs.get(r.text, [0, 0])
                all_docs[r.text][1] = r.score * self.keyword_weight
                
            # 排序
            results = [
                RetrievalResult(text=text, score=sum(scores), metadata={})
                for text, scores in all_docs.items()
            ]
            
            results.sort(key=lambda x: x.score, reverse=True)
            
            return results[:top_k]
