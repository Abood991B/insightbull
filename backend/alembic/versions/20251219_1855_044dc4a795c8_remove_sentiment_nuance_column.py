"""remove_sentiment_nuance_column

Revision ID: 044dc4a795c8
Revises: f28594a2c3ff
Create Date: 2025-12-19 18:55:49.973460+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '044dc4a795c8'
down_revision: Union[str, None] = 'f28594a2c3ff'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove sentiment_nuance column from sentiment_data table
    op.drop_column('sentiment_data', 'sentiment_nuance')


def downgrade() -> None:
    # Add sentiment_nuance column back if needed
    op.add_column('sentiment_data', sa.Column('sentiment_nuance', sa.String(length=50), nullable=True))
