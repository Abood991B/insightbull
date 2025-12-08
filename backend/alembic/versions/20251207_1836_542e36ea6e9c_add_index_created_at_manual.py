"""add_index_created_at_manual

Revision ID: 542e36ea6e9c
Revises: f4156dd5079a
Create Date: 2025-12-07 18:36:27.262128+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '542e36ea6e9c'
down_revision: Union[str, None] = 'f4156dd5079a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('idx_sentiment_created_at', 'sentiment_data', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_sentiment_created_at', table_name='sentiment_data')
