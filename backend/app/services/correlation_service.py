"""
Correlation calculation service for sentiment-price analysis
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import AsyncSessionLocal
from app.models import Stock, SentimentData, PriceData, CorrelationData
from app.core.websocket import emit_correlation_update

logger = logging.getLogger(__name__)


class CorrelationService:
    """Service for calculating sentiment-price correlations"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def calculate_all_correlations(self):
        """Calculate correlations for all active stocks"""
        try:
            # Get active stocks
            result = await self.session.execute(
                select(Stock).where(Stock.is_active == True)
            )
            stocks = result.scalars().all()
            
            logger.info(f"Calculating correlations for {len(stocks)} stocks")
            
            time_windows = ["1d", "7d", "14d"]
            
            for stock in stocks:
                for window in time_windows:
                    try:
                        await self.calculate_correlation(stock.symbol, window)
                    except Exception as e:
                        logger.error(f"Error calculating correlation for {stock.symbol} ({window}): {e}")
            
            await self.session.commit()
            logger.info("Correlation calculation completed")
            
        except Exception as e:
            logger.error(f"Correlation calculation failed: {e}")
            await self.session.rollback()
            raise
    
    async def calculate_correlation(
        self, 
        stock_symbol: str, 
        time_window: str = "7d"
    ) -> Optional[CorrelationData]:
        """Calculate correlation for a specific stock and time window"""
        try:
            # Parse time window
            days = {"1d": 1, "7d": 7, "14d": 14}.get(time_window, 7)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Get sentiment data
            sentiment_query = select(
                SentimentData.published_at,
                func.avg(SentimentData.sentiment_score).label("avg_sentiment")
            ).where(
                and_(
                    SentimentData.stock_symbol == stock_symbol,
                    SentimentData.published_at >= start_date,
                    SentimentData.published_at <= end_date
                )
            ).group_by(
                func.date_trunc('hour', SentimentData.published_at)
            ).order_by(SentimentData.published_at)
            
            sentiment_result = await self.session.execute(sentiment_query)
            sentiment_data = sentiment_result.all()
            
            if len(sentiment_data) < 3:
                logger.warning(f"Insufficient sentiment data for {stock_symbol} ({time_window})")
                return None
            
            # Get price data
            price_query = select(
                PriceData.date,
                PriceData.close
            ).where(
                and_(
                    PriceData.stock_symbol == stock_symbol,
                    PriceData.date >= start_date.date(),
                    PriceData.date <= end_date.date()
                )
            ).order_by(PriceData.date)
            
            price_result = await self.session.execute(price_query)
            price_data = price_result.all()
            
            if len(price_data) < 2:
                logger.warning(f"Insufficient price data for {stock_symbol} ({time_window})")
                return None
            
            # Align data by date
            aligned_data = self._align_data(sentiment_data, price_data)
            
            if len(aligned_data) < 3:
                logger.warning(f"Insufficient aligned data for {stock_symbol} ({time_window})")
                return None
            
            # Calculate correlation
            sentiments = [d['sentiment'] for d in aligned_data]
            prices = [d['price'] for d in aligned_data]
            
            # Normalize prices to percentage changes
            price_changes = []
            for i in range(1, len(prices)):
                change = (prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] != 0 else 0
                price_changes.append(change)
            
            # Align sentiment scores with price changes
            if len(sentiments) > len(price_changes):
                sentiments = sentiments[:len(price_changes)]
            
            # Calculate Pearson correlation
            if len(sentiments) >= 3 and len(price_changes) >= 3:
                correlation, p_value = stats.pearsonr(sentiments, price_changes)
                
                # Create or update correlation record
                existing = await self.session.execute(
                    select(CorrelationData).where(
                        and_(
                            CorrelationData.stock_symbol == stock_symbol,
                            CorrelationData.time_window == time_window
                        )
                    ).order_by(CorrelationData.calculated_at.desc()).limit(1)
                )
                correlation_record = existing.scalar_one_or_none()
                
                if correlation_record:
                    # Update existing record
                    correlation_record.correlation_coefficient = float(correlation)
                    correlation_record.p_value = float(p_value)
                    correlation_record.sample_size = len(sentiments)
                    correlation_record.calculated_at = datetime.utcnow()
                else:
                    # Create new record
                    correlation_record = CorrelationData(
                        stock_symbol=stock_symbol,
                        time_window=time_window,
                        correlation_coefficient=float(correlation),
                        p_value=float(p_value),
                        sample_size=len(sentiments),
                        calculated_at=datetime.utcnow()
                    )
                    self.session.add(correlation_record)
                
                await self.session.commit()
                
                # Emit WebSocket update
                await emit_correlation_update(stock_symbol, {
                    'correlation': float(correlation),
                    'p_value': float(p_value),
                    'time_window': time_window,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
                logger.info(f"Calculated correlation for {stock_symbol} ({time_window}): {correlation:.3f}")
                return correlation_record
            else:
                logger.warning(f"Not enough data points for correlation: {stock_symbol} ({time_window})")
                return None
            
        except Exception as e:
            logger.error(f"Error calculating correlation for {stock_symbol}: {e}")
            return None
    
    def _align_data(self, sentiment_data, price_data) -> list:
        """Align sentiment and price data by date"""
        aligned = []
        
        # Convert to dictionaries for easier lookup
        sentiment_by_date = {}
        for sent_time, sent_score in sentiment_data:
            date = sent_time.date()
            if date not in sentiment_by_date:
                sentiment_by_date[date] = []
            sentiment_by_date[date].append(float(sent_score))
        
        # Average sentiment scores per day
        for date in sentiment_by_date:
            sentiment_by_date[date] = np.mean(sentiment_by_date[date])
        
        # Align with price data
        for price_date, price in price_data:
            if price_date in sentiment_by_date:
                aligned.append({
                    'date': price_date,
                    'sentiment': sentiment_by_date[price_date],
                    'price': float(price)
                })
        
        return aligned
