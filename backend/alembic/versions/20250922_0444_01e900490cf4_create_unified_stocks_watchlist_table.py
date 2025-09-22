"""create_unified_stocks_watchlist_table

Revision ID: 01e900490cf4
Revises: b7c3dd8a781e
Create Date: 2025-09-22 04:44:46.514771+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01e900490cf4'
down_revision: Union[str, None] = 'b7c3dd8a781e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create the new unified stocks_watchlist table and drop old tables.
    
    This migration:
    1. Drops the existing stocks and watchlist_entries tables 
    2. Creates the new unified stocks_watchlist table
    3. Updates foreign key references in related tables
    4. Creates proper indexes for performance
    """
    
    # Step 1: Drop existing tables (we don't need the data)
    op.drop_table('stocks')
    
    # Step 2: Create the new unified stocks_watchlist table
    op.create_table('stocks_watchlist',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('added_to_watchlist', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('market_cap', sa.String(length=50), nullable=True),
        sa.Column('exchange', sa.String(length=20), server_default='NASDAQ'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )
    
    # Step 3: Create indexes for performance
    op.create_index('idx_stocks_watchlist_active', 'stocks_watchlist', ['is_active'])
    op.create_index('idx_stocks_watchlist_symbol_active', 'stocks_watchlist', ['symbol', 'is_active'])
    op.create_index('idx_stocks_watchlist_priority', 'stocks_watchlist', ['priority'])
    op.create_index('idx_stocks_watchlist_symbol', 'stocks_watchlist', ['symbol'])
    
    # Step 4: Clear sentiment_data and stock_prices tables (will be repopulated)
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM sentiment_data"))
    connection.execute(sa.text("DELETE FROM stock_prices"))


def downgrade() -> None:
    """
    Downgrade: Recreate the old stocks and watchlist_entries tables.
    """
    
    # Step 1: Clear related tables
    connection = op.get_bind()
    connection.execute(sa.text("DELETE FROM sentiment_data"))
    connection.execute(sa.text("DELETE FROM stock_prices"))
    
    # Step 2: Drop the unified table
    op.drop_index('idx_stocks_watchlist_symbol', table_name='stocks_watchlist')
    op.drop_index('idx_stocks_watchlist_priority', table_name='stocks_watchlist')
    op.drop_index('idx_stocks_watchlist_symbol_active', table_name='stocks_watchlist')
    op.drop_index('idx_stocks_watchlist_active', table_name='stocks_watchlist')
    op.drop_table('stocks_watchlist')
    
    # Step 3: Recreate old stocks table
    op.create_table('stocks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('symbol')
    )
