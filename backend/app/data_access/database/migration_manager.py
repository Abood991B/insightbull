"""
Database Migration Manager
=========================

Unified migration management using the data_access database system.
Provides CLI interface for database migrations and schema management.
"""

from typing import Optional, List
from pathlib import Path
import asyncio

from app.data_access.database.connection import init_database, get_db_session
from app.data_access.database.base import Base

# Use centralized logging system
from app.infrastructure.log_system import get_logger
logger = get_logger()


class MigrationManager:
    """Manages database migrations using SQLAlchemy."""
    
    def __init__(self):
        self.initialized = False
    
    async def initialize(self):
        """Initialize database connection."""
        if not self.initialized:
            await init_database()
            self.initialized = True
    
    async def create_all_tables(self):
        """Create all tables from models."""
        await self.initialize()
        logger.info("All tables created/verified successfully")
    
    async def drop_all_tables(self):
        """Drop all tables (WARNING: destroys all data)."""
        await self.initialize()
        
        async with get_db_session() as session:
            # Get engine from session
            engine = session.get_bind()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        
        logger.warning("All tables dropped - data destroyed!")
    
    async def reset_database(self):
        """Reset database by dropping and recreating all tables."""
        logger.warning("Resetting database - all data will be lost!")
        await self.drop_all_tables()
        await self.create_all_tables()
        logger.info("Database reset completed")
    
    def get_table_names(self) -> List[str]:
        """Get list of all table names from models."""
        return list(Base.metadata.tables.keys())
    
    def get_model_info(self) -> dict:
        """Get information about all models."""
        tables = {}
        for table_name, table in Base.metadata.tables.items():
            tables[table_name] = {
                'columns': [col.name for col in table.columns],
                'primary_keys': [col.name for col in table.primary_key],
                'foreign_keys': [fk.parent.name for fk in table.foreign_keys]
            }
        return tables