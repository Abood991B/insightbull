"""
Price data model for storing stock price information
"""
from sqlalchemy import Column, String, Numeric, Date, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import BaseModel


class PriceData(BaseModel):
    """Historical stock price data"""
    __tablename__ = "price_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_symbol = Column(String(10), ForeignKey("stocks.symbol"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(precision=10, scale=2))
    high = Column(Numeric(precision=10, scale=2))
    low = Column(Numeric(precision=10, scale=2))
    close = Column(Numeric(precision=10, scale=2), nullable=False)
    volume = Column(BigInteger)
    
    # Relationships
    stock = relationship("Stock", back_populates="price_data")
    
    def __repr__(self):
        return f"<PriceData {self.stock_symbol} - {self.date}: ${self.close}>"
