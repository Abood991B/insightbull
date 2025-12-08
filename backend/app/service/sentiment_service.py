"""
Sentiment Analysis Service
=========================

Business logic for sentiment analysis operations.
Implements sentiment data retrieval and analysis services.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc, or_
import structlog
import math
from app.utils.timezone import utc_now, to_naive_utc

from app.data_access.models import Stock, SentimentData, NewsArticle, HackerNewsPost
from app.infrastructure.log_system import get_logger


logger = get_logger()


# Temporal Decay Configuration
TEMPORAL_DECAY_HALF_LIFE_HOURS = 24  # Sentiment loses 50% weight after 24 hours
TEMPORAL_DECAY_ENABLED = True  # Master switch for temporal decay


class SentimentService:
    """
    Service class for sentiment analysis operations
    
    Handles business logic for:
    - Stock sentiment analysis
    - Sentiment trends over time
    - Source-specific sentiment breakdown
    - Recent mentions and data points
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger
        self.decay_enabled = TEMPORAL_DECAY_ENABLED
        self.decay_half_life = TEMPORAL_DECAY_HALF_LIFE_HOURS
    
    def _calculate_temporal_weight(self, timestamp: datetime, current_time: datetime = None) -> float:
        """
        Calculate temporal decay weight for sentiment data.
        
        Uses exponential decay: weight = exp(-hours_ago / half_life)
        
        Args:
            timestamp: When the sentiment was recorded
            current_time: Reference time (default: now)
            
        Returns:
            Weight between 0.0 and 1.0
            
        Examples:
            - 0 hours old: weight = 1.0 (100%)
            - 24 hours old: weight = 0.5 (50%)
            - 48 hours old: weight = 0.25 (25%)
            - 72 hours old: weight = 0.125 (12.5%)
        """
        if not self.decay_enabled:
            return 1.0  # No decay - all data has equal weight
        
        if current_time is None:
            current_time = utc_now()
        
        # Calculate hours since timestamp
        time_diff = current_time - timestamp
        hours_ago = time_diff.total_seconds() / 3600
        
        # Exponential decay: weight = exp(-hours_ago / half_life)
        # Using natural logarithm: exp(-ln(2) * hours_ago / half_life)
        decay_rate = math.log(2) / self.decay_half_life
        weight = math.exp(-decay_rate * hours_ago)
        
        # Cap minimum weight at 0.05 (5%) for very old data
        return max(weight, 0.05)

    async def get_sentiment_trends(self, stock_symbol: str, time_period: str = "7d") -> Dict[str, Any]:
        """
        Get sentiment trends for a specific stock.
        
        Implements U-FR3: Analyze Stock Sentiment
        """
        try:
            self.logger.info("Getting sentiment trends", stock_symbol=stock_symbol, time_period=time_period)
            
            # Get stock
            stock = await self._get_stock_by_symbol(stock_symbol)
            if not stock:
                return {
                    "stock_symbol": stock_symbol,
                    "time_period": time_period,
                    "sentiment_data": [],
                    "overall_sentiment": "neutral",
                    "confidence": 0.0,
                    "error": "Stock not found"
                }
            
            # Parse time period
            days = self._parse_time_period(time_period)
            cutoff_date = to_naive_utc(utc_now() - timedelta(days=days))
            
            # Get sentiment trends
            sentiment_data = await self._get_stock_sentiment_trends(stock.id, cutoff_date, days)
            
            # Calculate overall metrics
            overall_metrics = await self._get_overall_sentiment_metrics(stock.id, cutoff_date)
            
            return {
                "stock_symbol": stock_symbol,
                "stock_name": stock.name,
                "time_period": time_period,
                "sentiment_data": sentiment_data,
                "overall_sentiment": overall_metrics["sentiment_label"],
                "overall_score": overall_metrics["avg_sentiment"],
                "confidence": overall_metrics["avg_confidence"],
                "total_data_points": overall_metrics["total_count"]
            }
            
        except Exception as e:
            self.logger.error("Error getting sentiment trends", error=str(e))
            raise

    async def get_stock_sentiment_analysis(self, stock_symbol: str) -> Dict[str, Any]:
        """
        Get detailed sentiment analysis for a stock.
        
        Implements U-FR4: View Detailed Analysis
        """
        try:
            self.logger.info("Getting stock sentiment analysis", stock_symbol=stock_symbol)
            
            # Get stock
            stock = await self._get_stock_by_symbol(stock_symbol)
            if not stock:
                return {
                    "stock_symbol": stock_symbol,
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "source_breakdown": {},
                    "recent_mentions": [],
                    "error": "Stock not found"
                }
            
            # Get recent data (last 7 days)
            cutoff_date = to_naive_utc(utc_now() - timedelta(days=7))
            
            # Get overall metrics
            overall_metrics = await self._get_overall_sentiment_metrics(stock.id, cutoff_date)
            
            # Get source breakdown
            source_breakdown = await self._get_source_breakdown(stock.id, cutoff_date)
            
            # Get recent mentions
            recent_mentions = await self._get_recent_mentions(stock_symbol, cutoff_date)
            
            return {
                "stock_symbol": stock_symbol,
                "stock_name": stock.name,
                "sentiment_score": overall_metrics["avg_sentiment"],
                "confidence": overall_metrics["avg_confidence"],
                "total_data_points": overall_metrics["total_count"],
                "source_breakdown": source_breakdown,
                "recent_mentions": recent_mentions,
                "last_updated": utc_now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Error getting sentiment analysis", error=str(e))
            raise

    async def _get_stock_by_symbol(self, symbol: str) -> Optional[Stock]:
        """Get stock by symbol."""
        result = await self.db.execute(
            select(Stock).where(Stock.symbol == symbol.upper())
        )
        return result.scalar_one_or_none()

    async def _get_stock_sentiment_trends(self, stock_id: str, cutoff_date: datetime, days: int) -> List[Dict[str, Any]]:
        """Get sentiment trends over time for a stock."""
        try:
            # Determine time bucket size
            if days <= 1:
                interval = "hour"
            elif days <= 7:
                interval = "day"
            else:
                interval = "week"
            
            # Get sentiment data grouped by time intervals
            result = await self.db.execute(
                select(
                    func.date_trunc(interval, SentimentData.created_at).label('time_bucket'),
                    func.avg(SentimentData.sentiment_score).label('avg_sentiment'),
                    func.avg(SentimentData.confidence).label('avg_confidence'),
                    func.count().label('data_points'),
                    SentimentData.source
                )
                .where(and_(
                    SentimentData.stock_id == stock_id,
                    SentimentData.created_at >= cutoff_date
                ))
                .group_by(func.date_trunc(interval, SentimentData.created_at), SentimentData.source)
                .order_by(func.date_trunc(interval, SentimentData.created_at))
            )
            
            # Group by time bucket
            time_buckets = {}
            for row in result:
                bucket_key = row.time_bucket.isoformat()
                if bucket_key not in time_buckets:
                    time_buckets[bucket_key] = {
                        "timestamp": bucket_key,
                        "sources": {},
                        "overall_sentiment": 0.0,
                        "overall_confidence": 0.0,
                        "total_points": 0
                    }
                
                time_buckets[bucket_key]["sources"][row.source] = {
                    "sentiment_score": round(float(row.avg_sentiment), 3),
                    "confidence": round(float(row.avg_confidence), 3),
                    "data_points": int(row.data_points)
                }
            
            # Calculate overall metrics for each time bucket
            trends = []
            for bucket in time_buckets.values():
                total_sentiment = 0.0
                total_confidence = 0.0
                total_points = 0
                
                for source_data in bucket["sources"].values():
                    weight = source_data["data_points"]
                    total_sentiment += source_data["sentiment_score"] * weight
                    total_confidence += source_data["confidence"] * weight
                    total_points += weight
                
                if total_points > 0:
                    bucket["overall_sentiment"] = round(total_sentiment / total_points, 3)
                    bucket["overall_confidence"] = round(total_confidence / total_points, 3)
                    bucket["total_points"] = total_points
                
                trends.append(bucket)
            
            return sorted(trends, key=lambda x: x["timestamp"])
            
        except Exception as e:
            self.logger.error("Error getting sentiment trends", error=str(e))
            return []

    async def _get_overall_sentiment_metrics(self, stock_id: str, cutoff_date: datetime) -> Dict[str, Any]:
        """Get overall sentiment metrics for a stock with temporal decay."""
        try:
            # Fetch all sentiment data points
            result = await self.db.execute(
                select(SentimentData)
                .where(and_(
                    SentimentData.stock_id == stock_id,
                    SentimentData.processed_at >= cutoff_date
                ))
                .order_by(desc(SentimentData.processed_at))
            )
            
            sentiment_records = result.scalars().all()
            
            if not sentiment_records:
                return {
                    "avg_sentiment": 0.0,
                    "avg_confidence": 0.0,
                    "total_count": 0,
                    "sentiment_label": "neutral"
                }
            
            # Calculate time-weighted averages
            current_time = utc_now()
            weighted_sentiment_sum = 0.0
            weighted_confidence_sum = 0.0
            total_weight = 0.0
            
            for record in sentiment_records:
                # Calculate temporal weight
                weight = self._calculate_temporal_weight(record.processed_at, current_time)
                
                # Weighted sums
                weighted_sentiment_sum += record.sentiment_score * weight
                weighted_confidence_sum += record.confidence * weight
                total_weight += weight
            
            # Calculate weighted averages
            avg_sentiment = weighted_sentiment_sum / total_weight if total_weight > 0 else 0.0
            avg_confidence = weighted_confidence_sum / total_weight if total_weight > 0 else 0.0
            
            # Determine sentiment label
            if avg_sentiment > 0.1:
                sentiment_label = "positive"
            elif avg_sentiment < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            self.logger.debug(
                "Calculated time-weighted sentiment",
                extra={
                    "stock_id": stock_id,
                    "total_records": len(sentiment_records),
                    "total_weight": round(total_weight, 2),
                    "avg_sentiment": round(avg_sentiment, 3),
                    "decay_enabled": self.decay_enabled
                }
            )
            
            return {
                "avg_sentiment": round(avg_sentiment, 3),
                "avg_confidence": round(avg_confidence, 3),
                "total_count": len(sentiment_records),
                "sentiment_label": sentiment_label,
                "effective_weight": round(total_weight, 2)  # For debugging
            }
            
        except Exception as e:
            self.logger.error("Error getting overall sentiment metrics", error=str(e))
            return {
                "avg_sentiment": 0.0,
                "avg_confidence": 0.0,
                "total_count": 0,
                "sentiment_label": "neutral"
            }

    async def _get_source_breakdown(self, stock_id: str, cutoff_date: datetime) -> Dict[str, Dict[str, Any]]:
        """Get sentiment breakdown by source with temporal decay weighting."""
        try:
            # Fetch all sentiment data points grouped by source
            result = await self.db.execute(
                select(SentimentData)
                .where(and_(
                    SentimentData.stock_id == stock_id,
                    SentimentData.processed_at >= cutoff_date
                ))
                .order_by(desc(SentimentData.processed_at))
            )
            
            sentiment_records = result.scalars().all()
            
            if not sentiment_records:
                return {}
            
            # Group by source and calculate time-weighted averages
            current_time = utc_now()
            source_data = {}
            
            for record in sentiment_records:
                source = record.source
                if source not in source_data:
                    source_data[source] = {
                        "weighted_score_sum": 0.0,
                        "weighted_confidence_sum": 0.0,
                        "total_weight": 0.0,
                        "count": 0
                    }
                
                # Calculate temporal weight
                weight = self._calculate_temporal_weight(record.processed_at, current_time)
                
                # Accumulate weighted sums
                source_data[source]["weighted_score_sum"] += record.sentiment_score * weight
                source_data[source]["weighted_confidence_sum"] += record.confidence * weight
                source_data[source]["total_weight"] += weight
                source_data[source]["count"] += 1
            
            # Calculate final averages for each source
            breakdown = {}
            for source, data in source_data.items():
                if data["total_weight"] > 0:
                    breakdown[source] = {
                        "score": round(data["weighted_score_sum"] / data["total_weight"], 3),
                        "confidence": round(data["weighted_confidence_sum"] / data["total_weight"], 3),
                        "count": data["count"]
                    }
            
            return breakdown
            
        except Exception as e:
            self.logger.error("Error getting source breakdown", error=str(e))
            return {}

    async def _get_recent_mentions(self, stock_symbol: str, cutoff_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent mentions from news and HackerNews."""
        try:
            mentions = []
            
            # Get recent news articles
            news_result = await self.db.execute(
                select(NewsArticle)
                .where(and_(
                    NewsArticle.published_at >= cutoff_date,
                    or_(
                        NewsArticle.title.ilike(f"%{stock_symbol}%"),
                        NewsArticle.content.ilike(f"%{stock_symbol}%")
                    )
                ))
                .order_by(desc(NewsArticle.published_at))
                .limit(limit // 2)
            )
            
            for article in news_result.scalars():
                mentions.append({
                    "type": "news",
                    "title": article.title,
                    "content": article.content[:200] + "..." if len(article.content or "") > 200 else article.content,
                    "source": article.source,
                    "url": article.url,
                    "timestamp": article.published_at.isoformat(),
                    "sentiment_score": article.sentiment_score,
                    "confidence": article.confidence
                })
            
            # Get recent HackerNews posts
            hn_result = await self.db.execute(
                select(HackerNewsPost)
                .where(and_(
                    HackerNewsPost.created_utc >= cutoff_date,
                    or_(
                        HackerNewsPost.title.ilike(f"%{stock_symbol}%"),
                        HackerNewsPost.content.ilike(f"%{stock_symbol}%")
                    )
                ))
                .order_by(desc(HackerNewsPost.created_utc))
                .limit(limit // 2)
            )
            
            for post in hn_result.scalars():
                mentions.append({
                    "type": "hackernews",
                    "title": post.title,
                    "content": post.content[:200] + "..." if len(post.content or "") > 200 else post.content,
                    "source": "Hacker News",
                    "url": post.url or f"https://news.ycombinator.com/item?id={post.hn_id}",
                    "timestamp": post.created_utc.isoformat(),
                    "sentiment_score": post.sentiment_score,
                    "confidence": post.confidence,
                    "score": post.points,
                    "num_comments": post.num_comments
                })
            
            # Sort by timestamp and return most recent
            mentions.sort(key=lambda x: x["timestamp"], reverse=True)
            return mentions[:limit]
            
        except Exception as e:
            self.logger.error("Error getting recent mentions", error=str(e))
            return []

    def _parse_time_period(self, time_period: str) -> int:
        """Parse time period string to days."""
        period_map = {
            "1d": 1,
            "3d": 3,
            "7d": 7,
            "1w": 7,
            "2w": 14,
            "1m": 30,
            "3m": 90,
            "6m": 180,
            "1y": 365
        }
        return period_map.get(time_period, 7)  # Default to 7 days