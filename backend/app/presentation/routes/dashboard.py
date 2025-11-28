"""
Dashboard API Routes

Implements U-FR1: View Sentiment Dashboard
Provides dashboard overview with key metrics, top stocks, and system status.
"""

import logging
from datetime import datetime, timedelta
from app.utils.timezone import utc_now, to_naive_utc, ensure_utc
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.presentation.schemas import (
    DashboardSummary,
    MarketSentimentOverview,
    StockSummary,
    SystemStatus
)
from app.presentation.deps import (
    get_stock_repository,
    get_sentiment_repository,
    get_price_repository
)
from app.data_access.repositories import (
    StockRepository,
    SentimentDataRepository,
    StockPriceRepository
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def format_market_cap(market_cap_value: float) -> str:
    """
    Format market cap value from Yahoo Finance into readable string.
    
    Args:
        market_cap_value: Market cap in dollars (e.g., 2850000000000 for $2.85T)
    
    Returns:
        Formatted string (e.g., "2.85T", "150.5B", "5.2M")
    """
    if not market_cap_value or market_cap_value <= 0:
        return "N/A"
    
    # Trillions
    if market_cap_value >= 1_000_000_000_000:
        return f"{market_cap_value / 1_000_000_000_000:.2f}T"
    # Billions
    elif market_cap_value >= 1_000_000_000:
        return f"{market_cap_value / 1_000_000_000:.2f}B"
    # Millions
    elif market_cap_value >= 1_000_000:
        return f"{market_cap_value / 1_000_000:.2f}M"
    # Thousands
    else:
        return f"{market_cap_value / 1_000:.2f}K"


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    stock_repo: StockRepository = Depends(get_stock_repository),
    sentiment_repo: SentimentDataRepository = Depends(get_sentiment_repository),
    price_repo: StockPriceRepository = Depends(get_price_repository)
) -> DashboardSummary:
    """
    Get dashboard overview with key metrics - Implements U-FR1
    
    Returns:
        DashboardSummary: Complete dashboard data including:
        - Market sentiment overview
        - Top performing stocks
        - Recent price movers
        - System operational status
    """
    try:
        # Get market sentiment overview
        logger.info("Getting market sentiment overview...")
        market_overview = await _get_market_sentiment_overview(sentiment_repo, stock_repo)
        
        # Get top stocks by sentiment
        logger.info("Getting top stocks...")
        top_stocks = await _get_top_stocks_by_sentiment(stock_repo, sentiment_repo, price_repo, limit=10)
        
        # Get recent movers (stocks with significant price changes)
        logger.info("Getting recent movers...")
        recent_movers = await _get_recent_price_movers(stock_repo, price_repo, sentiment_repo, limit=5)
        
        # Get system status
        logger.info("Getting system status...")
        system_status = await _get_system_status(sentiment_repo, stock_repo)
        
        return DashboardSummary(
            market_overview=market_overview,
            top_stocks=top_stocks,
            recent_movers=recent_movers,
            system_status=system_status
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Dashboard summary error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dashboard summary: {str(e)}"
        )


async def _get_market_sentiment_overview(
    sentiment_repo: SentimentDataRepository,
    stock_repo: StockRepository
) -> MarketSentimentOverview:
    """Calculate market-wide sentiment metrics"""
    
    # Get recent sentiment data (last 24 hours)
    cutoff_time = to_naive_utc(utc_now() - timedelta(hours=24))
    
    # Calculate average sentiment across ACTIVE stocks only
    all_recent_sentiments = await sentiment_repo.get_recent_sentiment_scores(
        since=cutoff_time,
        limit=1000
    )
    
    # Get active stocks to filter sentiments
    all_stocks = await stock_repo.get_all()
    active_stock_ids = {s.id for s in all_stocks if s.is_active}
    
    # Filter sentiments to only include those from ACTIVE stocks
    recent_sentiments = [s for s in all_recent_sentiments if s.stock_id in active_stock_ids]
    
    if not recent_sentiments:
        # If no data in last 24 hours, try to get latest available sentiment data
        # This handles the case when pipeline hasn't run yet today after overnight shutdown
        logger.info("No sentiment data in last 24 hours, fetching latest available data...")
        
        # Try fetching sentiment from last 7 days as fallback
        fallback_cutoff = to_naive_utc(utc_now() - timedelta(days=7))
        fallback_sentiments = await sentiment_repo.get_recent_sentiment_scores(
            since=fallback_cutoff,
            limit=1000
        )
        
        # Filter to active stocks only
        recent_sentiments = [s for s in fallback_sentiments if s.stock_id in active_stock_ids]
        
        if not recent_sentiments:
            # Still no data - return default values
            # Only count ACTIVE stocks (not deactivated ones)
            total_stocks = len([s for s in all_stocks if s.is_active])
            logger.warning("No sentiment data available in last 7 days")
            return MarketSentimentOverview(
                average_sentiment=0.0,
                positive_stocks=0,
                neutral_stocks=0,
                negative_stocks=0,
                total_stocks=total_stocks,
                last_updated=utc_now()
            )
        
        logger.info(f"Using fallback sentiment data: {len(recent_sentiments)} records found")
    
    # Calculate sentiment distribution (only from ACTIVE stocks)
    sentiment_scores = [float(s.sentiment_score) for s in recent_sentiments]
    average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    # Count stocks by sentiment category
    positive_count = len([s for s in sentiment_scores if s > 0.1])
    negative_count = len([s for s in sentiment_scores if s < -0.1])
    neutral_count = len(sentiment_scores) - positive_count - negative_count
    
    # Total stocks count (already have all_stocks from above)
    total_stocks = len([s for s in all_stocks if s.is_active])
    
    return MarketSentimentOverview(
        average_sentiment=round(average_sentiment, 3),
        positive_stocks=positive_count,
        neutral_stocks=neutral_count,
        negative_stocks=negative_count,
        total_stocks=total_stocks,
        last_updated=utc_now()
    )


async def _get_top_stocks_by_sentiment(
    stock_repo: StockRepository,
    sentiment_repo: SentimentDataRepository,
    price_repo: StockPriceRepository,
    limit: int = 10
) -> List[StockSummary]:
    """
    Get top performing stocks by sentiment score with real-time prices from Yahoo Finance.
    
    ⚠️ CRITICAL: Prices are fetched directly from Yahoo Finance for accuracy:
    - current_price: Live market price or last closing price
    - price_change_24h: Calculated from Yahoo Finance previous close vs current price
    - Updates every 30 seconds during market hours
    
    Stock market hours: Monday-Friday 9:30 AM - 4:00 PM ET
    After hours: Uses last available closing price
    """
    
    all_stocks = await stock_repo.get_all()
    # Only process ACTIVE stocks (not deactivated ones)
    active_stocks = [s for s in all_stocks if s.is_active]
    stock_summaries = []
    
    # Import Yahoo Finance service for fresh price data
    import yfinance as yf
    
    for stock in active_stocks[:limit]:  # Limit processing for performance
        # Get latest sentiment
        latest_sentiment = await sentiment_repo.get_latest_sentiment_for_stock(stock.symbol)
        
        # 🔴 FETCH FRESH PRICES AND MARKET CAP DIRECTLY FROM YAHOO FINANCE
        current_price = None
        price_change_24h = None
        market_cap = None
        
        try:
            # Fetch live data from Yahoo Finance
            ticker = yf.Ticker(stock.symbol)
            info = ticker.info
            
            # Get current/latest price (prioritizes live data, falls back to previous close)
            current_price = (
                info.get('currentPrice') or      # Live price if market is open
                info.get('regularMarketPrice') or # Current/last trade price
                info.get('previousClose')         # Last closing price as fallback
            )
            
            # Get market cap from Yahoo Finance
            market_cap_raw = info.get('marketCap')
            market_cap = format_market_cap(market_cap_raw) if market_cap_raw else None
            
            if current_price:
                current_price = float(current_price)
                
                # Calculate 24-hour change using Yahoo Finance data
                previous_close = float(info.get('previousClose', current_price))
                
                if previous_close and previous_close > 0:
                    price_change_24h = ((current_price - previous_close) / previous_close) * 100
                    price_change_24h = round(price_change_24h, 2)
                
                logger.debug(f"{stock.symbol}: Current=${current_price:.2f}, Change={price_change_24h}%, MarketCap={market_cap}")
        
        except Exception as e:
            logger.warning(f"Error fetching live price for {stock.symbol} from Yahoo Finance: {e}")
            
            # Fallback to database if Yahoo Finance fails
            latest_price_record = await price_repo.get_latest_price_for_stock(stock.symbol)
            if latest_price_record:
                current_price = float(latest_price_record.close_price) if latest_price_record.close_price else None
                yesterday_price = await price_repo.get_price_at_time(
                    stock.symbol,
                    to_naive_utc(utc_now() - timedelta(hours=24))
                )
                if yesterday_price and yesterday_price.close_price and current_price:
                    price_change_24h = ((current_price - float(yesterday_price.close_price)) / float(yesterday_price.close_price)) * 100
                    price_change_24h = round(price_change_24h, 2)
        
        # Convert timestamp to aware UTC for proper API serialization
        last_updated_utc = ensure_utc(latest_sentiment.created_at) if latest_sentiment else None
        
        stock_summaries.append(StockSummary(
            symbol=stock.symbol,
            company_name=stock.name,  # Fixed: model uses 'name' not 'company_name'
            current_price=current_price,
            price_change_24h=price_change_24h,
            market_cap=market_cap,  # Real-time market cap from Yahoo Finance
            sentiment_score=round(float(latest_sentiment.sentiment_score), 3) if latest_sentiment else None,
            sentiment_label=latest_sentiment.sentiment_label if latest_sentiment else None,
            last_updated=last_updated_utc
        ))
    
    # Sort by sentiment score (descending)
    stock_summaries.sort(key=lambda x: x.sentiment_score or -1, reverse=True)
    
    return stock_summaries


async def _get_recent_price_movers(
    stock_repo: StockRepository,
    price_repo: StockPriceRepository,
    sentiment_repo: SentimentDataRepository,
    limit: int = 5
) -> List[StockSummary]:
    """
    Get stocks with significant recent price movements from Yahoo Finance.
    
    ⚠️ CRITICAL: Prices are fetched directly from Yahoo Finance:
    - Detects stocks with >2% price change in 24 hours
    - Uses real-time prices vs previous close
    - Accurate even outside market hours using last closing price
    """
    
    all_stocks = await stock_repo.get_all()
    # Only process ACTIVE stocks (not deactivated ones)
    active_stocks = [s for s in all_stocks if s.is_active]
    movers = []
    
    import yfinance as yf
    
    for stock in active_stocks:
        try:
            # 🔴 FETCH FRESH PRICES DIRECTLY FROM YAHOO FINANCE
            ticker = yf.Ticker(stock.symbol)
            info = ticker.info
            
            # Get current price
            current_price = (
                info.get('currentPrice') or
                info.get('regularMarketPrice') or
                info.get('previousClose')
            )
            
            if not current_price:
                continue
            
            current_price = float(current_price)
            previous_close = float(info.get('previousClose', current_price))
            
            # Get market cap from Yahoo Finance
            market_cap_raw = info.get('marketCap')
            market_cap = format_market_cap(market_cap_raw) if market_cap_raw else None
            
            # Calculate 24-hour change from previous close
            if previous_close and previous_close > 0:
                price_change = ((current_price - previous_close) / previous_close) * 100
            else:
                continue
            
            # Only include significant movers (>2% change)
            if abs(price_change) > 2.0:
                # Get latest sentiment
                latest_sentiment = await sentiment_repo.get_latest_sentiment_for_stock(stock.symbol)
                
                logger.debug(f"{stock.symbol}: MOVER! ${current_price:.2f} ({price_change:+.2f}%), MarketCap={market_cap}")
                
                # Convert timestamp to aware UTC for proper API serialization
                last_updated_utc = ensure_utc(latest_sentiment.created_at) if latest_sentiment else None
                
                movers.append(StockSummary(
                    symbol=stock.symbol,
                    company_name=stock.name,
                    current_price=current_price,
                    price_change_24h=round(price_change, 2),
                    market_cap=market_cap,  # Real-time market cap from Yahoo Finance
                    sentiment_score=round(float(latest_sentiment.sentiment_score), 3) if latest_sentiment else None,
                    sentiment_label=latest_sentiment.sentiment_label if latest_sentiment else None,
                    last_updated=last_updated_utc
                ))
        
        except Exception as e:
            logger.warning(f"Error fetching price mover data for {stock.symbol}: {e}")
            # Fallback to database if Yahoo Finance fails
            try:
                latest_price = await price_repo.get_latest_price_for_stock(stock.symbol)
                if not latest_price:
                    continue
                
                yesterday_price = await price_repo.get_price_at_time(
                    stock.symbol,
                    to_naive_utc(utc_now() - timedelta(hours=24))
                )
                
                if not yesterday_price:
                    continue
                
                # Calculate price change from database
                price_change = ((float(latest_price.close_price) - float(yesterday_price.close_price)) / float(yesterday_price.close_price)) * 100
                
                # Only include significant movers
                if abs(price_change) > 2.0:
                    latest_sentiment = await sentiment_repo.get_latest_sentiment_for_stock(stock.symbol)
                    
                    # Convert timestamp to aware UTC for proper API serialization
                    last_updated_utc = ensure_utc(latest_price.price_timestamp)
                    
                    movers.append(StockSummary(
                        symbol=stock.symbol,
                        company_name=stock.name,
                        current_price=float(latest_price.close_price),
                        price_change_24h=round(price_change, 2),
                        market_cap=None,  # Market cap unavailable in database fallback
                        sentiment_score=round(float(latest_sentiment.sentiment_score), 3) if latest_sentiment else None,
                        sentiment_label=latest_sentiment.sentiment_label if latest_sentiment else None,
                        last_updated=last_updated_utc
                    ))
            except Exception as db_e:
                logger.error(f"Database fallback failed for {stock.symbol}: {db_e}")
                continue
    
    # Sort by absolute price change (descending)
    movers.sort(key=lambda x: abs(x.price_change_24h or 0), reverse=True)
    
    return movers[:limit]


async def _get_system_status(
    sentiment_repo: SentimentDataRepository,
    stock_repo: StockRepository
) -> SystemStatus:
    """Get current system operational status"""
    
    # Get last collection time
    latest_sentiment = await sentiment_repo.get_latest_sentiment()
    last_collection = latest_sentiment.created_at if latest_sentiment else None
    
    # Determine pipeline status
    if last_collection:
        # Convert naive datetime from DB to aware UTC for comparison
        now_utc = utc_now()
        last_collection_utc = ensure_utc(last_collection)
        
        hours_since_update = (now_utc - last_collection_utc).total_seconds() / 3600
        if hours_since_update < 2:
            pipeline_status = "operational"
        elif hours_since_update < 6:
            pipeline_status = "delayed"
        else:
            pipeline_status = "stale"
    else:
        pipeline_status = "no_data"
    
    # Get total sentiment records count
    total_records = await sentiment_repo.get_total_count()
    
    # Active data sources - all 4 sources
    active_sources = ["HackerNews", "NewsAPI", "FinHub", "Marketaux"]
    
    # Convert last_collection to aware UTC for proper API serialization
    last_collection_aware = ensure_utc(last_collection) if last_collection else None
    
    return SystemStatus(
        pipeline_status=pipeline_status,
        last_collection=last_collection_aware,
        active_data_sources=active_sources,
        total_sentiment_records=total_records
    )