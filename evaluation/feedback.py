"""Feedback Collection and Analysis - 用户反馈收集与分析"""
import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, Counter
import statistics

logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """反馈类型"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"


class FeedbackSentiment(Enum):
    """反馈情感"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class Feedback:
    """用户反馈"""
    id: str
    task_id: str
    user_id: str
    feedback_type: FeedbackType
    rating: Optional[int] = None
    comment: Optional[str] = None
    sentiment: FeedbackSentiment = FeedbackSentiment.NEUTRAL
    category: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "feedback_type": self.feedback_type.value,
            "rating": self.rating,
            "comment": self.comment,
            "sentiment": self.sentiment.value,
            "category": self.category,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat()
        }


@dataclass
class FeedbackAnalysis:
    """反馈分析结果"""
    total_feedback: int = 0
    positive_count: int = 0
    negative_count: int = 0
    neutral_count: int = 0
    avg_rating: float = 0.0
    sentiment_distribution: Dict = field(default_factory=dict)
    category_distribution: Dict = field(default_factory=dict)
    tag_frequency: Dict = field(default_factory=dict)
    rating_distribution: Dict = field(default_factory=dict)
    time_series: List[Dict] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "total_feedback": self.total_feedback,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "avg_rating": self.avg_rating,
            "sentiment_distribution": self.sentiment_distribution,
            "category_distribution": self.category_distribution,
            "tag_frequency": self.tag_frequency,
            "rating_distribution": self.rating_distribution,
            "time_series": self.time_series,
            "insights": self.insights
        }


class FeedbackCollector:
    """反馈收集器"""
    
    def __init__(self, storage_path: str = "./feedback_data"):
        self.storage_path = storage_path
        self._feedback_store: Dict[str, Feedback] = {}
        self._task_feedback: Dict[str, List[str]] = defaultdict(list)
        self._user_feedback: Dict[str, List[str]] = defaultdict(list)
        self._lock = asyncio.Lock()
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储"""
        import os
        os.makedirs(self.storage_path, exist_ok=True)
    
    async def collect(
        self,
        task_id: str,
        user_id: str,
        feedback_type: FeedbackType,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None
    ) -> Feedback:
        """收集反馈"""
        async with self._lock:
            feedback_id = f"fb_{int(time.time() * 1000)}"
            
            sentiment = self._analyze_sentiment(comment, feedback_type)
            
            feedback = Feedback(
                id=feedback_id,
                task_id=task_id,
                user_id=user_id,
                feedback_type=feedback_type,
                rating=rating,
                comment=comment,
                sentiment=sentiment,
                category=category,
                tags=tags or [],
                metadata=metadata or {}
            )
            
            self._feedback_store[feedback_id] = feedback
            self._task_feedback[task_id].append(feedback_id)
            self._user_feedback[user_id].append(feedback_id)
            
            await self._persist_feedback(feedback)
            
            logger.info(f"Collected feedback: {feedback_id} (type={feedback_type.value})")
            
            return feedback
    
    def _analyze_sentiment(
        self,
        comment: Optional[str],
        feedback_type: FeedbackType
    ) -> FeedbackSentiment:
        """分析情感"""
        if feedback_type == FeedbackType.POSITIVE:
            return FeedbackSentiment.POSITIVE
        elif feedback_type == FeedbackType.NEGATIVE:
            return FeedbackSentiment.NEGATIVE
        elif feedback_type == FeedbackType.BUG_REPORT:
            return FeedbackSentiment.NEGATIVE
        
        if comment:
            positive_words = {'good', 'great', 'excellent', 'amazing', 'wonderful', 'perfect', 'love', 'best'}
            negative_words = {'bad', 'poor', 'terrible', 'awful', 'worst', 'hate', 'wrong', 'issue', 'problem'}
            
            comment_lower = comment.lower()
            
            pos_count = sum(1 for w in positive_words if w in comment_lower)
            neg_count = sum(1 for w in negative_words if w in comment_lower)
            
            if pos_count > neg_count:
                return FeedbackSentiment.POSITIVE
            elif neg_count > pos_count:
                return FeedbackSentiment.NEGATIVE
        
        return FeedbackSentiment.NEUTRAL
    
    async def _persist_feedback(self, feedback: Feedback):
        """持久化反馈"""
        import os
        filepath = os.path.join(self.storage_path, f"{feedback.id}.json")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(feedback.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist feedback: {e}")
    
    async def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """获取反馈"""
        return self._feedback_store.get(feedback_id)
    
    async def get_task_feedback(self, task_id: str) -> List[Feedback]:
        """获取任务的反馈"""
        feedback_ids = self._task_feedback.get(task_id, [])
        return [self._feedback_store[fid] for fid in feedback_ids if fid in self._feedback_store]
    
    async def get_user_feedback(self, user_id: str) -> List[Feedback]:
        """获取用户的反馈"""
        feedback_ids = self._user_feedback.get(user_id, [])
        return [self._feedback_store[fid] for fid in feedback_ids if fid in self._feedback_store]
    
    async def get_recent_feedback(
        self,
        limit: int = 100,
        feedback_type: Optional[FeedbackType] = None,
        since: Optional[datetime] = None
    ) -> List[Feedback]:
        """获取最近的反馈"""
        feedbacks = list(self._feedback_store.values())
        
        if feedback_type:
            feedbacks = [f for f in feedbacks if f.feedback_type == feedback_type]
        
        if since:
            feedbacks = [f for f in feedbacks if f.created_at >= since]
        
        feedbacks.sort(key=lambda f: f.created_at, reverse=True)
        
        return feedbacks[:limit]
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """删除反馈"""
        async with self._lock:
            if feedback_id not in self._feedback_store:
                return False
            
            feedback = self._feedback_store[feedback_id]
            
            del self._feedback_store[feedback_id]
            self._task_feedback[feedback.task_id].remove(feedback_id)
            self._user_feedback[feedback.user_id].remove(feedback_id)
            
            import os
            filepath = os.path.join(self.storage_path, f"{feedback_id}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return True
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        return {
            "total_feedback": len(self._feedback_store),
            "unique_tasks": len(self._task_feedback),
            "unique_users": len(self._user_feedback)
        }


class FeedbackAnalyzer:
    """反馈分析器"""
    
    def __init__(self, collector: FeedbackCollector):
        self.collector = collector
    
    async def analyze(
        self,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        user_ids: Optional[List[str]] = None,
        task_ids: Optional[List[str]] = None
    ) -> FeedbackAnalysis:
        """分析反馈"""
        feedbacks = list(self.collector._feedback_store.values())
        
        if since:
            feedbacks = [f for f in feedbacks if f.created_at >= since]
        if until:
            feedbacks = [f for f in feedbacks if f.created_at <= until]
        if user_ids:
            feedbacks = [f for f in feedbacks if f.user_id in user_ids]
        if task_ids:
            feedbacks = [f for f in feedbacks if f.task_id in task_ids]
        
        analysis = FeedbackAnalysis()
        analysis.total_feedback = len(feedbacks)
        
        if not feedbacks:
            return analysis
        
        for fb in feedbacks:
            if fb.sentiment == FeedbackSentiment.POSITIVE:
                analysis.positive_count += 1
            elif fb.sentiment == FeedbackSentiment.NEGATIVE:
                analysis.negative_count += 1
            else:
                analysis.neutral_count += 1
            
            if fb.category:
                analysis.category_distribution[fb.category] = \
                    analysis.category_distribution.get(fb.category, 0) + 1
            
            for tag in fb.tags:
                analysis.tag_frequency[tag] = analysis.tag_frequency.get(tag, 0) + 1
            
            if fb.rating is not None:
                analysis.rating_distribution[fb.rating] = \
                    analysis.rating_distribution.get(fb.rating, 0) + 1
        
        analysis.sentiment_distribution = {
            "positive": analysis.positive_count,
            "negative": analysis.negative_count,
            "neutral": analysis.neutral_count
        }
        
        ratings = [f.rating for f in feedbacks if f.rating is not None]
        if ratings:
            analysis.avg_rating = statistics.mean(ratings)
        
        analysis.time_series = self._generate_time_series(feedbacks)
        
        analysis.insights = self._generate_insights(analysis)
        
        return analysis
    
    def _generate_time_series(self, feedbacks: List[Feedback]) -> List[Dict]:
        """生成时间序列"""
        if not feedbacks:
            return []
        
        feedbacks_sorted = sorted(feedbacks, key=lambda f: f.created_at)
        
        daily_counts = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
        
        for fb in feedbacks_sorted:
            date_key = fb.created_at.strftime("%Y-%m-%d")
            daily_counts[date_key][fb.sentiment.value] += 1
        
        time_series = [
            {
                "date": date,
                "positive": counts["positive"],
                "negative": counts["negative"],
                "neutral": counts["neutral"],
                "total": sum(counts.values())
            }
            for date, counts in sorted(daily_counts.items())
        ]
        
        return time_series
    
    def _generate_insights(self, analysis: FeedbackAnalysis) -> List[str]:
        """生成洞察"""
        insights = []
        
        if analysis.total_feedback == 0:
            insights.append("No feedback data available for analysis")
            return insights
        
        if analysis.avg_rating > 4:
            insights.append(f"Average rating is high ({analysis.avg_rating:.1f}/5)")
        elif analysis.avg_rating < 3:
            insights.append(f"Average rating is low ({analysis.avg_rating:.1f}/5)")
        
        positive_rate = analysis.positive_count / analysis.total_feedback
        if positive_rate > 0.7:
            insights.append("Overall sentiment is predominantly positive")
        elif positive_rate < 0.4:
            insights.append("Overall sentiment needs attention - more negative than positive")
        
        if analysis.category_distribution:
            top_category = max(analysis.category_distribution.items(), key=lambda x: x[1])
            insights.append(f"Most common feedback category: {top_category[0]}")
        
        if analysis.tag_frequency:
            top_tags = sorted(analysis.tag_frequency.items(), key=lambda x: x[1], reverse=True)[:3]
            tag_names = [t[0] for t in top_tags]
            insights.append(f"Most frequent tags: {', '.join(tag_names)}")
        
        return insights
    
    async def get_trend(
        self,
        metric: str = "sentiment",
        window_days: int = 7
    ) -> Dict:
        """获取趋势"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=window_days)
        
        analysis = await self.analyze(since=start_date, until=end_date)
        
        if metric == "sentiment":
            return {
                "metric": "sentiment",
                "window_days": window_days,
                "positive_rate": analysis.positive_count / analysis.total_feedback if analysis.total_feedback > 0 else 0,
                "negative_rate": analysis.negative_count / analysis.total_feedback if analysis.total_feedback > 0 else 0,
                "neutral_rate": analysis.neutral_count / analysis.total_feedback if analysis.total_feedback > 0 else 0,
                "time_series": analysis.time_series
            }
        elif metric == "rating":
            return {
                "metric": "rating",
                "window_days": window_days,
                "avg_rating": analysis.avg_rating,
                "distribution": analysis.rating_distribution
            }
        
        return {}


class FeedbackLoop:
    """反馈循环 - 基于反馈优化系统"""
    
    def __init__(self, collector: FeedbackCollector, analyzer: FeedbackAnalyzer):
        self.collector = collector
        self.analyzer = analyzer
        self._optimization_rules: List[Callable] = []
    
    def add_optimization_rule(self, rule: Callable):
        """添加优化规则"""
        self._optimization_rules.append(rule)
    
    async def analyze_and_optimize(self) -> Dict:
        """分析并优化"""
        analysis = await self.analyzer.analyze()
        
        recommendations = []
        
        for rule in self._optimization_rules:
            try:
                result = rule(analysis)
                if result:
                    recommendations.append(result)
            except Exception as e:
                logger.error(f"Optimization rule failed: {e}")
        
        if analysis.negative_count > analysis.positive_count * 0.5:
            recommendations.append({
                "type": "attention_needed",
                "message": "Negative feedback threshold exceeded, review required"
            })
        
        if analysis.avg_rating < 3.0 and analysis.avg_rating > 0:
            recommendations.append({
                "type": "low_rating",
                "message": f"Average rating ({analysis.avg_rating:.1f}) below threshold"
            })
        
        return {
            "analysis": analysis.to_dict(),
            "recommendations": recommendations,
            "rules_applied": len(self._optimization_rules)
        }
