"""
Database Retry Utilities

Handles database operations with retry logic for SQLite lock errors.
"""

import asyncio
import structlog
from typing import Callable, Any
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


async def retry_on_db_lock(
    operation: Callable[[], Any],
    max_retries: int = 3,
    base_delay: float = 0.5,
    operation_name: str = "database operation"
) -> Any:
    """
    Retry a database operation with exponential backoff on lock errors.
    
    Args:
        operation: Async callable to execute (e.g., session.commit)
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        operation_name: Name of operation for logging
        
    Returns:
        Result of the operation
        
    Raises:
        OperationalError: If max retries exceeded or non-lock error
    """
    for attempt in range(max_retries):
        try:
            result = await operation()
            if attempt > 0:
                logger.info(
                    f"{operation_name} succeeded after retry",
                    attempt=attempt + 1,
                    max_retries=max_retries
                )
            return result
        except OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                retry_delay = base_delay * (2 ** attempt)
                logger.warning(
                    f"{operation_name} - database locked, retrying",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    retry_delay=retry_delay
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"{operation_name} failed after retries",
                    error=str(e),
                    attempts=attempt + 1,
                    max_retries=max_retries
                )
                raise


async def commit_with_retry(
    session: AsyncSession,
    max_retries: int = 3,
    base_delay: float = 0.5
) -> None:
    """
    Commit database session with retry logic for lock errors.
    
    Args:
        session: SQLAlchemy async session to commit
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds for exponential backoff
        
    Raises:
        OperationalError: If commit fails after all retries
    """
    await retry_on_db_lock(
        operation=lambda: session.commit(),
        max_retries=max_retries,
        base_delay=base_delay,
        operation_name="commit"
    )
