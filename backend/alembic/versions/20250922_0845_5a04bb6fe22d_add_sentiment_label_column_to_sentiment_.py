"""add_sentiment_label_column_to_sentiment_data

Revision ID: 5a04bb6fe22d
Revises: 01e900490cf4
Create Date: 2025-09-22 08:45:21.982969+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a04bb6fe22d'
down_revision: Union[str, None] = '01e900490cf4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sentiment_label column with default value 'Neutral'
    op.add_column('sentiment_data', sa.Column('sentiment_label', sa.String(20), nullable=False, default='Neutral'))
    
    # Create index on sentiment_label for better query performance
    op.create_index('ix_sentiment_data_sentiment_label', 'sentiment_data', ['sentiment_label'])


def downgrade() -> None:
    # Drop the index first
    op.drop_index('ix_sentiment_data_sentiment_label', 'sentiment_data')
    
    # Drop the sentiment_label column
    op.drop_column('sentiment_data', 'sentiment_label')
