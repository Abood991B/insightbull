"""
Dashboard API Routes

Implements U-FR1: View Sentiment Dashboard
Provides dashboard overview with key metrics, top stocks, and system status.
"""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.presentation.schemas import (
    DashboardSummary,
    MarketSentimentOverview,
    StockSummary,
    SystemStatus
)
from app.presentation.deps import (
    get_db,
    get_stock_repository,
    get_sentiment_repository,
    get_price_repository
)
from app.data_access.repositories import (
    StockRepository,
    SentimentDataRepository,
    StockPriceRepository
)
from app.data_access.models import Stock, SentimentData, StockPrice

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


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
        market_overview = await _get_market_sentiment_overview(sentiment_repo, stock_repo)
        
        # Get top stocks by sentiment
        top_stocks = await _get_top_stocks_by_sentiment(stock_repo, sentiment_repo, price_repo, limit=10)
        
        # Get recent movers (stocks with significant price changes)
        recent_movers = await _get_recent_price_movers(stock_repo, price_repo, sentiment_repo, limit=5)
        
        # Get system status
        system_status = await _get_system_status(sentiment_repo, stock_repo)
        
        return DashboardSummary(
            market_overview=market_overview,
            top_stocks=top_stocks,
            recent_movers=recent_movers,
            system_status=system_status
        )
        
    except Exception as e:
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
    cutoff_time = datetime.utcnow() - timedelta(hours=24)
    
    # Calculate average sentiment across all stocks
    recent_sentiments = await sentiment_repo.get_recent_sentiment_scores(
        since=cutoff_time,
        limit=1000
    )
    
    if not recent_sentiments:
        # Return default values if no recent data
        total_stocks = len(await stock_repo.get_all())
        return MarketSentimentOverview(
            average_sentiment=0.0,
            positive_stocks=0,
            neutral_stocks=0,
            negative_stocks=0,
            total_stocks=total_stocks,
            last_updated=datetime.utcnow()
        )
    
    # Calculate sentiment distribution
    sentiment_scores = [s.score for s in recent_sentiments]
    average_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    # Count stocks by sentiment category
    positive_count = len([s for s in sentiment_scores if s > 0.1])
    negative_count = len([s for s in sentiment_scores if s < -0.1])
    neutral_count = len(sentiment_scores) - positive_count - negative_count
    
    total_stocks = len(await stock_repo.get_all())
    
    return MarketSentimentOverview(
        average_sentiment=round(average_sentiment, 3),
        positive_stocks=positive_count,
        neutral_stocks=neutral_count,
        negative_stocks=negative_count,
        total_stocks=total_stocks,
        last_updated=datetime.utcnow()
    )


async def _get_top_stocks_by_sentiment(
    stock_repo: StockRepository,
    sentiment_repo: SentimentDataRepository,
    price_repo: StockPriceRepository,
    limit: int = 10
) -> List[StockSummary]:
    """Get top performing stocks by sentiment score"""
    
    stocks = await stock_repo.get_all()
    stock_summaries = []
    
    for stock in stocks[:limit]:  # Limit processing for performance
        # Get latest sentiment
        latest_sentiment = await sentiment_repo.get_latest_sentiment_for_stock(stock.symbol)
        
        # Get latest price
        latest_price_record = await price_repo.get_latest_price_for_stock(stock.symbol)
        
        # Calculate 24h price change
        price_change_24h = None
        current_price = None
        
        if latest_price_record:
            current_price = latest_price_record.close_price
            yesterday_price = await price_repo.get_price_at_time(
                stock.symbol,
                datetime.utcnow() - timedelta(hours=24)
            )
            if yesterday_price:
                price_change_24h = ((current_price - yesterday_price.close_price) / yesterday_price.close_price) * 100
        
        stock_summaries.append(StockSummary(
            symbol=stock.symbol,
            company_name=stock.company_name,
            current_price=current_price,
            price_change_24h=round(price_change_24h, 2) if price_change_24h else None,
            sentiment_score=round(latest_sentiment.score, 3) if latest_sentiment else None,
            sentiment_label=latest_sentiment.label if latest_sentiment else None,
            last_updated=latest_sentiment.timestamp if latest_sentiment else None
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
    """Get stocks with significant recent price movements"""
    
    stocks = await stock_repo.get_all()
    movers = []
    
    for stock in stocks:
        # Get current and previous day prices
        latest_price = await price_repo.get_latest_price_for_stock(stock.symbol)
        if not latest_price:
            continue
            
        yesterday_price = await price_repo.get_price_at_time(
            stock.symbol,
            datetime.utcnow() - timedelta(hours=24)
        )
        
        if not yesterday_price:
            continue
            
        # Calculate price change
        price_change = ((latest_price.close_price - yesterday_price.close_price) / yesterday_price.close_price) * 100
        
        # Only include significant movers (>2% change)
        if abs(price_change) > 2.0:
            # Get latest sentiment
            latest_sentiment = await sentiment_repo.get_latest_sentiment_for_stock(stock.symbol)
            
            movers.append(StockSummary(
                symbol=stock.symbol,
                company_name=stock.company_name,
                current_price=latest_price.close_price,
                price_change_24h=round(price_change, 2),
                sentiment_score=round(latest_sentiment.score, 3) if latest_sentiment else None,
                sentiment_label=latest_sentiment.label if latest_sentiment else None,
                last_updated=latest_price.timestamp
            ))
    
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
    last_collection = latest_sentiment.timestamp if latest_sentiment else None
    
    # Determine pipeline status
    if last_collection:
        hours_since_update = (datetime.utcnow() - last_collection).total_seconds() / 3600
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
    
    # Active data sources (this would be expanded with actual source monitoring)
    active_sources = ["reddit", "news"]  # Simplified for now
    
    return SystemStatus(
        pipeline_status=pipeline_status,
        last_collection=last_collection,
        active_data_sources=active_sources,
        total_sentiment_records=total_records
    )