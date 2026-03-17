"""Metrics - 评估指标集合"""
import re
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from collections import Counter
import math

logger = logging.getLogger(__name__)


class BaseMetric:
    """基础指标类"""
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
    
    def compute(self, prompt: str, output: str, context: Dict) -> float:
        """计算指标（同步）"""
        raise NotImplementedError
    
    async def compute_async(self, prompt: str, output: str, context: Dict) -> float:
        """计算指标（异步）"""
        return self.compute(prompt, output, context)


class RelevanceMetric(BaseMetric):
    """相关性指标 - 评估输出与输入的相关程度"""
    
    def __init__(self, min_length: int = 10, keyword_weight: float = 0.5):
        super().__init__("relevance", "Measures how relevant the output is to the input prompt")
        self.min_length = min_length
        self.keyword_weight = keyword_weight
    
    def compute(self, prompt: str, output: str, context: Dict) -> float:
        """计算相关性分数"""
        if not output or len(output.strip()) < self.min_length:
            return 0.0
        
        prompt_lower = prompt.lower()
        output_lower = output.lower()
        
        prompt_words = set(self._tokenize(prompt_lower))
        output_words = set(self._tokenize(output_lower))
        
        if not prompt_words:
            return 0.5
        
        overlap = prompt_words & output_words
        keyword_score = len(overlap) / len(prompt_words)
        
        length_score = min(len(output) / 500, 1.0)
        
        semantic_score = self._check_semantic_alignment(prompt, output)
        
        final_score = (
            keyword_score * self.keyword_weight +
            length_score * (1 - self.keyword_weight) * 0.3 +
            semantic_score * (1 - self.keyword_weight) * 0.7
        )
        
        return min(max(final_score, 0.0), 1.0)
    
    def _tokenize(self, text: str) -> List[str]:
        """分词"""
        text = re.sub(r'[^\w\s]', ' ', text)
        return [w for w in text.split() if len(w) > 2]
    
    def _check_semantic_alignment(self, prompt: str, output: str) -> float:
        """语义对齐检查"""
        prompt_keywords = self._extract_keywords(prompt)
        output_keywords = self._extract_keywords(output)
        
        if not prompt_keywords:
            return 0.5
        
        matches = sum(1 for kw in prompt_keywords if kw in output_keywords)
        return matches / len(prompt_keywords)
    
    def _extract_keywords(self, text: str) -> Set[str]:
        """提取关键词"""
        words = self._tokenize(text.lower())
        word_freq = Counter(words)
        
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
                    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
                    'would', 'could', 'should', 'may', 'might', 'must', 'shall'}
        
        keywords = {w for w, c in word_freq.items() 
                  if c >= 2 and w not in stopwords}
        return keywords


class CoherenceMetric(BaseMetric):
    """连贯性指标 - 评估输出内容的逻辑连贯性"""
    
    def __init__(self, min_sentences: int = 2):
        super().__init__("coherence", "Measures the logical coherence of the output")
        self.min_sentences = min_sentences
    
    def compute(self, prompt: str, output: str, context: Dict) -> float:
        """计算连贯性分数"""
        sentences = self._split_sentences(output)
        
        if len(sentences) < self.min_sentences:
            return 0.5 if sentences else 0.0
        
        transition_score = self._analyze_transitions(sentences)
        pronoun_score = self._analyze_pronouns(sentences)
        structure_score = self._analyze_structure(sentences)
        
        final_score = (
            transition_score * 0.4 +
            pronoun_score * 0.3 +
            structure_score * 0.3
        )
        
        return min(max(final_score, 0.0), 1.0)
    
    def _split_sentences(self, text: str) -> List[str]:
        """分割句子"""
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _analyze_transitions(self, sentences: List[str]) -> float:
        """分析过渡词"""
        transition_words = {
            'however', 'therefore', 'moreover', 'furthermore', 'consequently',
            'nevertheless', 'thus', 'hence', 'accordingly', 'additionally',
            'meanwhile', 'subsequently', 'otherwise', 'instead', 'although'
        }
        
        transitions_found = 0
        for sentence in sentences:
            words = set(sentence.lower().split())
            if words & transition_words:
                transitions_found += 1
        
        return transitions_found / len(sentences) if sentences else 0.0
    
    def _analyze_pronouns(self, sentences: List[str]) -> float:
        """分析代词使用"""
        pronouns = {'it', 'they', 'them', 'this', 'that', 'these', 'those', 'he', 'she'}
        
        if len(sentences) < 2:
            return 0.5
        
        valid_refs = 0
        for i, sentence in enumerate(sentences[1:], 1):
            words = set(sentence.lower().split())
            if words & pronouns:
                valid_refs += 1
        
        return valid_refs / (len(sentences) - 1) if len(sentences) > 1 else 0.5
    
    def _analyze_structure(self, sentences: List[str]) -> float:
        """分析句子结构"""
        lengths = [len(s.split()) for s in sentences]
        
        if not lengths:
            return 0.0
        
        avg_length = sum(lengths) / len(lengths)
        variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        
        if avg_length == 0:
            return 0.0
        
        cv = std_dev / avg_length
        
        if cv < 0.3:
            return 1.0
        elif cv < 0.6:
            return 0.7
        elif cv < 1.0:
            return 0.4
        return 0.2


class ToxicityMetric(BaseMetric):
    """毒性指标 - 检测有害内容"""
    
    TOXIC_PATTERNS = [
        r'\b(hate|kill|murder|attack|harm|threat|abuse)\b',
        r'\b(insult|ridicule|humiliate|discriminat)\b',
        r'\b(sexist|racist|homophobic|xenophobic)\b',
    ]
    
    def __init__(self, threshold: float = 0.3):
        super().__init__("toxicity", "Detects potentially toxic or harmful content")
        self.threshold = threshold
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.TOXIC_PATTERNS]
    
    def compute(self, prompt: str, output: str, context: Dict) -> float:
        """计算毒性分数（越低越好，返回 1 - toxicity）"""
        toxicity_score = self._detect_toxicity(output)
        
        return 1.0 - min(toxicity_score, 1.0)
    
    def _detect_toxicity(self, text: str) -> float:
        """检测毒性"""
        text_lower = text.lower()
        
        matches = 0
        total_patterns = len(self._compiled_patterns)
        
        for pattern in self._compiled_patterns:
            if pattern.search(text_lower):
                matches += 1
        
        return matches / total_patterns


class FluencyMetric(BaseMetric):
    """流畅性指标 - 评估语言流畅程度"""
    
    def __init__(self):
        super().__init__("fluency", "Measures the fluency of the output text")
        self._init_language_model()
    
    def _init_language_model(self):
        """初始化简单语言模型"""
        self.common_words = {
            'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
            'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
            'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she'
        }
    
    def compute(self, prompt: str, output: str, context: Dict) -> float:
        """计算流畅性分数"""
        if not output or len(output.strip()) < 10:
            return 0.0
        
        words = output.split()
        
        if not words:
            return 0.0
        
        word_count_score = min(len(words) / 100, 1.0)
        
        vocab_richness = self._calculate_vocab_richness(words)
        
        grammar_score = self._check_basic_grammar(output)
        
        final_score = (
            word_count_score * 0.2 +
            vocab_richness * 0.4 +
            grammar_score * 0.4
        )
        
        return min(max(final_score, 0.0), 1.0)
    
    def _calculate_vocab_richness(self, words: List[str]) -> float:
        """计算词汇丰富度"""
        if not words:
            return 0.0
        
        unique_words = len(set(words))
        total_words = len(words)
        
        return unique_words / total_words if total_words > 0 else 0.0
    
    def _check_basic_grammar(self, text: str) -> float:
        """检查基本语法"""
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.5
        
        valid_sentences = 0
        for sentence in sentences:
            words = sentence.split()
            if len(words) >= 3:
                valid_sentences += 1
        
        return valid_sentences / len(sentences)


class AccuracyMetric(BaseMetric):
    """准确性指标 - 评估事实准确性"""
    
    def __init__(self, facts: Optional[List[str]] = None):
        super().__init__("accuracy", "Measures factual accuracy of the output")
        self.facts = facts or []
    
    def compute(self, prompt: str, output: str, context: Dict) -> float:
        """计算准确性分数"""
        if not self.facts:
            return 0.5
        
        matches = 0
        for fact in self.facts:
            if fact.lower() in output.lower():
                matches += 1
        
        return matches / len(self.facts)


class SafetyMetric(BaseMetric):
    """安全性指标 - 评估输出安全性"""
    
    def __init__(self):
        super().__init__("safety", "Evaluates output safety")
        self._dangerous_patterns = [
            r'sql\s*injection',
            r'xss',
            r'<script',
            r'eval\s*\(',
            r'exec\s*\(',
            r'rm\s+-rf',
            r'drop\s+table',
        ]
        self._compiled = [re.compile(p, re.IGNORECASE) for p in self._dangerous_patterns]
    
    def compute(self, prompt: str, output: str, context: Dict) -> float:
        """计算安全性分数"""
        output_lower = output.lower()
        
        for pattern in self._compiled:
            if pattern.search(output_lower):
                return 0.0
        
        return 1.0


class MetricFactory:
    """指标工厂"""
    
    _metrics = {
        "relevance": RelevanceMetric,
        "coherence": CoherenceMetric,
        "toxicity": ToxicityMetric,
        "fluency": FluencyMetric,
        "accuracy": AccuracyMetric,
        "safety": SafetyMetric,
    }
    
    @classmethod
    def create(cls, name: str, **kwargs) -> BaseMetric:
        """创建指标实例"""
        if name not in cls._metrics:
            raise ValueError(f"Unknown metric: {name}. Available: {list(cls._metrics.keys())}")
        
        return cls._metrics[name](**kwargs)
    
    @classmethod
    def create_all(cls, config: Optional[Dict[str, Dict]] = None) -> Dict[str, BaseMetric]:
        """创建所有默认指标"""
        config = config or {}
        metrics = {}
        
        for name, metric_class in cls._metrics.items():
            kwargs = config.get(name, {})
            metrics[name] = metric_class(**kwargs)
        
        return metrics
    
    @classmethod
    def register(cls, name: str, metric_class: type):
        """注册新的指标类型"""
        cls._metrics[name] = metric_class
        logger.info(f"Registered new metric: {name}")
    
    @classmethod
    def available_metrics(cls) -> List[str]:
        """获取可用指标列表"""
        return list(cls._metrics.keys())
