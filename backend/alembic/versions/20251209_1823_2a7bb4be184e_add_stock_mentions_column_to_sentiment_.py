"""Add stock_mentions column to sentiment_data

Revision ID: 2a7bb4be184e
Revises: 542e36ea6e9c
Create Date: 2025-12-09 18:23:51.029706+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2a7bb4be184e'
down_revision: Union[str, None] = '542e36ea6e9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add stock_mentions column to sentiment_data table
    # This column stores an array of stock symbols mentioned in the content
    # that generated the sentiment (e.g., ["AAPL", "MSFT"])
    op.add_column('sentiment_data', sa.Column('stock_mentions', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove stock_mentions column from sentiment_data table
    op.drop_column('sentiment_data', 'stock_mentions')
