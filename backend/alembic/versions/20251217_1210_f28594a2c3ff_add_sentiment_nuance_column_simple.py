"""Add sentiment_nuance column simple

Revision ID: f28594a2c3ff
Revises: 7d0cd94f5f31
Create Date: 2025-12-17 12:10:57.442039+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f28594a2c3ff'
down_revision: Union[str, None] = '542e36ea6e9c'  # Current head
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sentiment_nuance column to sentiment_data table
    op.add_column('sentiment_data', sa.Column('sentiment_nuance', sa.String(length=50), nullable=True))


def downgrade() -> None:
    # Remove sentiment_nuance column
    op.drop_column('sentiment_data', 'sentiment_nuance')
