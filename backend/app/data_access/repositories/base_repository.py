"""
Simple Repository Pattern Implementation

Basic repository class implementing the Repository Pattern for data access abstraction.
Aligned with FYP layered architecture requirements.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional, Dict, Any, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

if TYPE_CHECKING:
    from app.data_access.database.base import Base

# Generic type for model classes
ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType], ABC):
    """
    Base repository class providing basic CRUD operations
    
    Simple implementation of the Repository Pattern for the FYP project.
    """
    
    def __init__(self, model: type[ModelType], db_session: AsyncSession):
        """
        Initialize repository with model class and database session
        
        Args:
            model: SQLAlchemy model class
            db_session: Async database session
        """
        self.model = model
        self.db_session = db_session
    
    async def create(self, obj_data: Dict[str, Any]) -> ModelType:
        """Create a new record"""
        db_obj = self.model(**obj_data)
        self.db_session.add(db_obj)
        await self.db_session.flush()  # Let context manager handle commit
        await self.db_session.refresh(db_obj)
        return db_obj
    
    async def get_by_id(self, obj_id: uuid.UUID) -> Optional[ModelType]:
        """Get record by ID"""
        result = await self.db_session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self) -> List[ModelType]:
        """Get all records"""
        result = await self.db_session.execute(select(self.model))
        return result.scalars().all()
    
    async def update(self, obj_id: uuid.UUID, obj_data: Dict[str, Any]) -> Optional[ModelType]:
        """Update a record"""
        db_obj = await self.get_by_id(obj_id)
        if db_obj:
            for field, value in obj_data.items():
                setattr(db_obj, field, value)
            await self.db_session.flush()  # Let context manager handle commit
            await self.db_session.refresh(db_obj)
        return db_obj
    
    async def delete(self, obj_id: uuid.UUID) -> bool:
        """Delete a record"""
        db_obj = await self.get_by_id(obj_id)
        if db_obj:
            await self.db_session.delete(db_obj)
            await self.db_session.commit()
            return True
        return False