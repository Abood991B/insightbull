"""
Dashboard Service
================

Business logic for dashboard operations.
Implements dashboard data aggregation and presentation services.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text, and_, desc
import structlog

from app.data_access.models import Stock, SentimentData, StockPrice, NewsArticle, RedditPost
from app.infrastructure.log_system import get_logger


logger = get_logger()


class DashboardService:
    """
    Service class for dashboard operations
    
    Handles business logic for:
    - Sentiment overview aggregation
    - Stock performance data
    - News summaries
    - Time-based filtering
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger

    async def get_dashboard_overview(self, time_period: str = "7d") -> Dict[str, Any]:
        """
        Get comprehensive dashboard overview with real data.
        
        Implements U-FR1: View Sentiment Dashboard
        """
        try:
            self.logger.info("Getting dashboard overview", time_period=time_period)
            
            # Parse time period
            days = self._parse_time_period(time_period)
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get overall sentiment metrics
            sentiment_overview = await self._get_sentiment_overview(cutoff_date)
            
            # Get stock data with latest sentiment
            stock_data = await self._get_stock_data(cutoff_date)
            
            # Get sentiment trends over time
            sentiment_trends = await self._get_sentiment_trends(cutoff_date, days)
            
            # Get news summary
            news_summary = await self._get_news_summary(cutoff_date)
            
            return {
                "sentiment_overview": sentiment_overview,
                "time_period": time_period,
                "stock_data": stock_data,
                "sentiment_trends": sentiment_trends,
                "news_summary": news_summary,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Error getting dashboard overview", error=str(e))
            raise

    async def _get_sentiment_overview(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Get overall sentiment metrics."""
        try:
            # Get recent sentiment data
            result = await self.db.execute(
                select(
                    func.avg(SentimentData.sentiment_score).label('avg_sentiment'),
                    func.avg(SentimentData.confidence).label('avg_confidence'),
                    func.count().label('total_count')
                )
                .where(SentimentData.processed_at >= cutoff_date)
            )
            
            metrics = result.first()
            
            if not metrics or metrics.total_count == 0:
                return {
                    "overall_sentiment": "neutral",
                    "sentiment_score": 0.0,
                    "confidence": 0.0,
                    "total_data_points": 0
                }
            
            avg_sentiment = float(metrics.avg_sentiment or 0.0)
            avg_confidence = float(metrics.avg_confidence or 0.0)
            
            # Determine sentiment label
            if avg_sentiment > 0.1:
                sentiment_label = "positive"
            elif avg_sentiment < -0.1:
                sentiment_label = "negative"
            else:
                sentiment_label = "neutral"
            
            return {
                "overall_sentiment": sentiment_label,
                "sentiment_score": round(avg_sentiment, 3),
                "confidence": round(avg_confidence, 3),
                "total_data_points": int(metrics.total_count)
            }
            
        except Exception as e:
            self.logger.error("Error getting sentiment overview", error=str(e))
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "confidence": 0.0,
                "total_data_points": 0
            }

    async def _get_stock_data(self, cutoff_date: datetime, limit: int = 20) -> List[Dict[str, Any]]:
        """Get stock data with latest sentiment and price info."""
        try:
            # Get stocks with their latest sentiment data
            result = await self.db.execute(
                select(
                    Stock.symbol,
                    Stock.name,
                    Stock.sector,
                    func.avg(SentimentData.sentiment_score).label('avg_sentiment'),
                    func.avg(SentimentData.confidence).label('avg_confidence'),
                    func.count(SentimentData.id).label('sentiment_count')
                )
                .outerjoin(SentimentData, and_(
                    Stock.id == SentimentData.stock_id,
                    SentimentData.processed_at >= cutoff_date
                ))
                .group_by(Stock.symbol, Stock.name, Stock.sector)
                .order_by(desc(func.count(SentimentData.id)))
                .limit(limit)
            )
            
            stocks = []
            for row in result:
                sentiment_score = float(row.avg_sentiment or 0.0)
                confidence = float(row.avg_confidence or 0.0)
                
                stocks.append({
                    "symbol": row.symbol,
                    "name": row.name,
                    "sector": row.sector,
                    "sentiment_score": round(sentiment_score, 3),
                    "confidence": round(confidence, 3),
                    "data_points": int(row.sentiment_count),
                    "trend": "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral"
                })
            
            return stocks
            
        except Exception as e:
            self.logger.error("Error getting stock data", error=str(e))
            return []

    async def _get_sentiment_trends(self, cutoff_date: datetime, days: int) -> List[Dict[str, Any]]:
        """Get sentiment trends over time."""
        try:
            # Create date buckets based on time period
            if days <= 1:
                interval = "1 hour"
                date_format = "%Y-%m-%d %H:00"
            elif days <= 7:
                interval = "1 day"
                date_format = "%Y-%m-%d"
            else:
                interval = "1 week"
                date_format = "%Y-W%U"
            
            # Get sentiment trends grouped by time intervals
            result = await self.db.execute(
                text(f"""
                    SELECT 
                        DATE_TRUNC('{interval.split()[1]}', processed_at) as time_bucket,
                        AVG(sentiment_score) as avg_sentiment,
                        AVG(confidence) as avg_confidence,
                        COUNT(*) as data_points
                    FROM sentiment_data 
                    WHERE processed_at >= :cutoff_date
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """),
                {"cutoff_date": cutoff_date}
            )
            
            trends = []
            for row in result:
                trends.append({
                    "timestamp": row.time_bucket.isoformat(),
                    "sentiment_score": round(float(row.avg_sentiment), 3),
                    "confidence": round(float(row.avg_confidence), 3),
                    "data_points": int(row.data_points)
                })
            
            return trends
            
        except Exception as e:
            self.logger.error("Error getting sentiment trends", error=str(e))
            return []

    async def _get_news_summary(self, cutoff_date: datetime) -> Dict[str, Any]:
        """Get news articles summary."""
        try:
            # Get news article counts and sentiment distribution
            result = await self.db.execute(
                select(
                    func.count().label('total_articles'),
                    func.sum(func.case((NewsArticle.sentiment_score > 0.1, 1), else_=0)).label('positive'),
                    func.sum(func.case((NewsArticle.sentiment_score < -0.1, 1), else_=0)).label('negative'),
                    func.sum(func.case((and_(NewsArticle.sentiment_score >= -0.1, NewsArticle.sentiment_score <= 0.1), 1), else_=0)).label('neutral')
                )
                .where(NewsArticle.published_at >= cutoff_date)
            )
            
            summary = result.first()
            
            if not summary or summary.total_articles == 0:
                return {
                    "total_articles": 0,
                    "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                    "sources": []
                }
            
            # Get source breakdown
            source_result = await self.db.execute(
                select(
                    NewsArticle.source,
                    func.count().label('count')
                )
                .where(NewsArticle.published_at >= cutoff_date)
                .group_by(NewsArticle.source)
                .order_by(desc(func.count()))
                .limit(5)
            )
            
            sources = [{"name": row.source, "count": int(row.count)} for row in source_result]
            
            return {
                "total_articles": int(summary.total_articles),
                "sentiment_distribution": {
                    "positive": int(summary.positive or 0),
                    "neutral": int(summary.neutral or 0),
                    "negative": int(summary.negative or 0)
                },
                "sources": sources
            }
            
        except Exception as e:
            self.logger.error("Error getting news summary", error=str(e))
            return {
                "total_articles": 0,
                "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
                "sources": []
            }

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