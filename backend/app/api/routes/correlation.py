"""
Correlation analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Literal, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models import CorrelationData, Stock
from app.schemas.correlation import CorrelationResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{symbol}")
async def get_correlation(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    time_window: Literal["1d", "7d", "14d"] = Query("7d")
):
    """Get sentiment-price correlation for a stock"""
    try:
        # Get the most recent correlation data
        query = select(CorrelationData).where(
            and_(
                CorrelationData.stock_symbol == symbol.upper(),
                CorrelationData.time_window == time_window
            )
        ).order_by(desc(CorrelationData.calculated_at)).limit(1)
        
        result = await db.execute(query)
        correlation = result.scalar_one_or_none()
        
        if not correlation:
            # Trigger correlation calculation
            from app.services.correlation_service import CorrelationService
            service = CorrelationService()
            correlation = await service.calculate_correlation(symbol.upper(), time_window)
            
            if not correlation:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Insufficient data to calculate correlation for {symbol}"
                )
        
        # Check if correlation is stale (older than 1 hour)
        if correlation.calculated_at < datetime.utcnow() - timedelta(hours=1):
            # Trigger recalculation in background
            from app.services.correlation_service import CorrelationService
            service = CorrelationService()
            # This would ideally be done in a background task
            correlation = await service.calculate_correlation(symbol.upper(), time_window)
        
        return {
            "symbol": correlation.stock_symbol,
            "time_window": correlation.time_window,
            "correlation_coefficient": float(correlation.correlation_coefficient),
            "p_value": float(correlation.p_value) if correlation.p_value else None,
            "sample_size": correlation.sample_size,
            "calculated_at": correlation.calculated_at,
            "strength": _get_correlation_strength(correlation.correlation_coefficient),
            "interpretation": _interpret_correlation(correlation.correlation_coefficient)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching correlation: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch correlation data")


@router.get("/")
async def get_all_correlations(
    db: AsyncSession = Depends(get_db),
    time_window: Literal["1d", "7d", "14d"] = Query("7d"),
    min_correlation: Optional[float] = Query(None, ge=-1, le=1)
):
    """Get correlations for all stocks"""
    try:
        # Get latest correlation for each stock
        subquery = select(
            CorrelationData.stock_symbol,
            func.max(CorrelationData.calculated_at).label("latest_calc")
        ).where(
            CorrelationData.time_window == time_window
        ).group_by(CorrelationData.stock_symbol).subquery()
        
        query = select(CorrelationData).join(
            subquery,
            and_(
                CorrelationData.stock_symbol == subquery.c.stock_symbol,
                CorrelationData.calculated_at == subquery.c.latest_calc,
                CorrelationData.time_window == time_window
            )
        )
        
        if min_correlation is not None:
            query = query.where(
                func.abs(CorrelationData.correlation_coefficient) >= abs(min_correlation)
            )
        
        result = await db.execute(query.order_by(desc(CorrelationData.correlation_coefficient)))
        correlations = result.scalars().all()
        
        return [
            {
                "symbol": c.stock_symbol,
                "time_window": c.time_window,
                "correlation_coefficient": float(c.correlation_coefficient),
                "p_value": float(c.p_value) if c.p_value else None,
                "sample_size": c.sample_size,
                "calculated_at": c.calculated_at,
                "strength": _get_correlation_strength(c.correlation_coefficient),
                "interpretation": _interpret_correlation(c.correlation_coefficient)
            }
            for c in correlations
        ]
        
    except Exception as e:
        logger.error(f"Error fetching all correlations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch correlation data")


def _get_correlation_strength(correlation: float) -> str:
    """Determine correlation strength"""
    abs_corr = abs(correlation)
    if abs_corr >= 0.7:
        return "strong"
    elif abs_corr >= 0.4:
        return "moderate"
    elif abs_corr >= 0.2:
        return "weak"
    else:
        return "negligible"


def _interpret_correlation(correlation: float) -> str:
    """Interpret correlation value"""
    if correlation >= 0.7:
        return "Strong positive correlation - sentiment and price move together"
    elif correlation >= 0.4:
        return "Moderate positive correlation - sentiment somewhat predicts price"
    elif correlation >= 0.2:
        return "Weak positive correlation - slight relationship"
    elif correlation >= -0.2:
        return "No significant correlation"
    elif correlation >= -0.4:
        return "Weak negative correlation - slight inverse relationship"
    elif correlation >= -0.7:
        return "Moderate negative correlation - sentiment inversely related to price"
    else:
        return "Strong negative correlation - sentiment and price move oppositely"
