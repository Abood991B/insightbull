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
from app.utils.timezone import utc_now, to_naive_utc

from app.data_access.models import Stock, SentimentData, NewsArticle, RedditPost
from app.infrastructure.log_system import get_logger


logger = get_logger()


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
        """Get overall sentiment metrics for a stock."""
        try:
            result = await self.db.execute(
                select(
                    func.avg(SentimentData.sentiment_score).label('avg_sentiment'),
                    func.avg(SentimentData.confidence).label('avg_confidence'),
                    func.count().label('total_count')
                )
                .where(and_(
                    SentimentData.stock_id == stock_id,
                    SentimentData.processed_at >= cutoff_date
                ))
            )
            
            metrics = result.first()
            
            if not metrics or metrics.total_count == 0:
                return {
                    "avg_sentiment": 0.0,
                    "avg_confidence": 0.0,
                    "total_count": 0,
                    "sentiment_label": "neutral"
                }
            
            avg_sentiment = float(metrics.avg_sentiment or 0.0)
            
            # Determine sentiment label
            if avg_sentiment > 0.1:
                sentiment_label = "positive"
            elif avg_sentiment < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            return {
                "avg_sentiment": round(avg_sentiment, 3),
                "avg_confidence": round(float(metrics.avg_confidence or 0.0), 3),
                "total_count": int(metrics.total_count),
                "sentiment_label": sentiment_label
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
        """Get sentiment breakdown by source."""
        try:
            result = await self.db.execute(
                select(
                    SentimentData.source,
                    func.avg(SentimentData.sentiment_score).label('avg_score'),
                    func.avg(SentimentData.confidence).label('avg_confidence'),
                    func.count().label('count')
                )
                .where(and_(
                    SentimentData.stock_id == stock_id,
                    SentimentData.processed_at >= cutoff_date
                ))
                .group_by(SentimentData.source)
            )
            
            breakdown = {}
            for row in result:
                breakdown[row.source] = {
                    "score": round(float(row.avg_score), 3),
                    "confidence": round(float(row.avg_confidence), 3),
                    "count": int(row.count)
                }
            
            return breakdown
            
        except Exception as e:
            self.logger.error("Error getting source breakdown", error=str(e))
            return {}

    async def _get_recent_mentions(self, stock_symbol: str, cutoff_date: datetime, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent mentions from news and reddit."""
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
            
            # Get recent reddit posts
            reddit_result = await self.db.execute(
                select(RedditPost)
                .where(and_(
                    RedditPost.created_utc >= cutoff_date,
                    or_(
                        RedditPost.title.ilike(f"%{stock_symbol}%"),
                        RedditPost.content.ilike(f"%{stock_symbol}%")
                    )
                ))
                .order_by(desc(RedditPost.created_utc))
                .limit(limit // 2)
            )
            
            for post in reddit_result.scalars():
                mentions.append({
                    "type": "reddit",
                    "title": post.title,
                    "content": post.content[:200] + "..." if len(post.content or "") > 200 else post.content,
                    "source": f"r/{post.subreddit}",
                    "url": post.url,
                    "timestamp": post.created_utc.isoformat(),
                    "sentiment_score": post.sentiment_score,
                    "confidence": post.confidence,
                    "score": post.score,
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