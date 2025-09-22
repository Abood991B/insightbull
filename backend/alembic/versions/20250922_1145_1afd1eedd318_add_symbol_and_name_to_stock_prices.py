"""add_symbol_and_name_to_stock_prices

Revision ID: 1afd1eedd318
Revises: 04d86b22534f
Create Date: 2025-09-22 11:45:11.558459+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1afd1eedd318'
down_revision: Union[str, None] = '04d86b22534f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if columns already exist before adding them
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('stock_prices')]
    
    # Add symbol column only if it doesn't exist
    if 'symbol' not in columns:
        op.add_column('stock_prices', sa.Column('symbol', sa.String(20), nullable=True))
    
    # Add name column only if it doesn't exist  
    if 'name' not in columns:
        op.add_column('stock_prices', sa.Column('name', sa.String(200), nullable=True))
    
    # Check if index exists before creating it
    indexes = [idx['name'] for idx in inspector.get_indexes('stock_prices')]
    if 'idx_stock_prices_symbol' not in indexes:
        op.create_index('idx_stock_prices_symbol', 'stock_prices', ['symbol'])
    
    # Update existing records with symbol and name from stocks_watchlist
    op.execute("""
        UPDATE stock_prices 
        SET symbol = sw.symbol, name = sw.name 
        FROM stocks_watchlist sw 
        WHERE stock_prices.stock_id = sw.id 
        AND (stock_prices.symbol IS NULL OR stock_prices.name IS NULL)
    """)
    
    # Note: SQLite doesn't support ALTER COLUMN to change nullability
    # The symbol column will remain nullable, but the application will ensure it's populated


def downgrade() -> None:
    # Check what exists before trying to drop
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Drop index if it exists
    indexes = [idx['name'] for idx in inspector.get_indexes('stock_prices')]
    if 'idx_stock_prices_symbol' in indexes:
        op.drop_index('idx_stock_prices_symbol', 'stock_prices')
    
    # Drop columns if they exist
    columns = [col['name'] for col in inspector.get_columns('stock_prices')]
    if 'name' in columns:
        op.drop_column('stock_prices', 'name')
    if 'symbol' in columns:
        op.drop_column('stock_prices', 'symbol')
