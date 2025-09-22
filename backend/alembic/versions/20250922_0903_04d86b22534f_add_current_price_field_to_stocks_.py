"""add_current_price_field_to_stocks_watchlist

Revision ID: 04d86b22534f
Revises: 5a04bb6fe22d
Create Date: 2025-09-22 09:03:31.886739+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '04d86b22534f'
down_revision: Union[str, None] = '5a04bb6fe22d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add current_price column to stocks_watchlist table
    op.add_column('stocks_watchlist', sa.Column('current_price', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove current_price column from stocks_watchlist table
    op.drop_column('stocks_watchlist', 'current_price')
