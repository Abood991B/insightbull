"""
Model metrics for tracking sentiment analysis model performance
"""
from sqlalchemy import Column, String, Float, Integer, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel


class ModelMetric(BaseModel):
    """Performance metrics for sentiment analysis models"""
    __tablename__ = "model_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(50), nullable=False)  # 'finbert', 'vader'
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    f1_score = Column(Float)
    evaluation_date = Column(Date, nullable=False)
    test_size = Column(Integer)
    
    def __repr__(self):
        return f"<ModelMetric {self.model_name} - Accuracy: {self.accuracy:.2%}>"
