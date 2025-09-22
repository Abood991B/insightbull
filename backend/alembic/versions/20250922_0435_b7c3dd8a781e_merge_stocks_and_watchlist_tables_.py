"""merge_stocks_and_watchlist_tables_properly

Revision ID: b7c3dd8a781e
Revises: e61438baa56b
Create Date: 2025-09-22 04:35:15.532179+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7c3dd8a781e'
down_revision: Union[str, None] = 'e61438baa56b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Properly merge stocks and watchlist_entries tables into a unified stocks table.
    
    This migration recreates the stocks table with the unified schema due to SQLite limitations.
    """
    
    connection = op.get_bind()
    
    # Step 1: Create new unified stocks table
    op.create_table('stocks_new',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('symbol', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('added_to_watchlist', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Step 2: Migrate data from old stocks table and merge with watchlist_entries
    connection.execute(sa.text("""
        INSERT INTO stocks_new (id, symbol, name, sector, is_active, added_to_watchlist, priority, created_at, updated_at)
        SELECT 
            s.id,
            s.symbol,
            s.name,
            s.sector,
            COALESCE(w.is_active, false) as is_active,
            COALESCE(w.added_date, s.created_at) as added_to_watchlist,
            COALESCE(w.priority, 0) as priority,
            s.created_at,
            s.updated_at
        FROM stocks s
        LEFT JOIN watchlist_entries w ON s.id = w.stock_id
    """))
    
    # Step 3: Drop old tables and rename new one
    op.drop_table('stocks')
    op.rename_table('stocks_new', 'stocks')
    
    # Step 4: Drop the watchlist_entries table (no longer needed)
    op.drop_index('idx_watchlist_stock_active', table_name='watchlist_entries')
    op.drop_index('idx_watchlist_active', table_name='watchlist_entries')
    op.drop_table('watchlist_entries')
    
    # Step 5: Create indexes for performance
    op.create_index('idx_stock_active', 'stocks', ['is_active'])
    op.create_index('idx_stock_symbol_active', 'stocks', ['symbol', 'is_active'])


def downgrade() -> None:
    """
    Downgrade: Split the unified stocks table back into stocks and watchlist_entries.
    """
    
    # Step 1: Recreate the watchlist_entries table
    op.create_table('watchlist_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('stock_id', sa.UUID(), nullable=False),
        sa.Column('added_date', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['stock_id'], ['stocks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Step 2: Create indexes
    op.create_index('idx_watchlist_active', 'watchlist_entries', ['is_active'])
    op.create_index('idx_watchlist_stock_active', 'watchlist_entries', ['stock_id', 'is_active'])
    
    # Step 3: Migrate active stocks back to watchlist_entries
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO watchlist_entries (id, stock_id, added_date, is_active, priority)
        SELECT 
            lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-' || 
            lower(hex(randomblob(2))) || '-' || lower(hex(randomblob(2))) || '-' || 
            lower(hex(randomblob(6))) as id,
            id as stock_id,
            added_to_watchlist as added_date,
            is_active,
            priority
        FROM stocks 
        WHERE is_active = true
    """))
    
    # Step 4: Drop watchlist fields from stocks table
    op.drop_index('idx_stock_symbol_active', table_name='stocks')
    op.drop_index('idx_stock_active', table_name='stocks')
    op.drop_column('stocks', 'priority')
    op.drop_column('stocks', 'added_to_watchlist')
    op.drop_column('stocks', 'is_active')
