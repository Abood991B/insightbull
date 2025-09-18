"""add_model_used_column_to_sentiment_data

Revision ID: 27a0e45223fc
Revises: 8653cc238299
Create Date: 2025-09-18 12:13:56.354654+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27a0e45223fc'
down_revision: Union[str, None] = '8653cc238299'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the model_used column (nullable first, then we'll populate and make it non-nullable)
    op.add_column('sentiment_data', sa.Column('model_used', sa.String(50), nullable=True))
    
    # Update existing records to extract model_used from extra_data JSON
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE sentiment_data 
        SET model_used = JSON_EXTRACT(extra_data, '$.model_used')
        WHERE extra_data IS NOT NULL 
        AND JSON_EXTRACT(extra_data, '$.model_used') IS NOT NULL
    """))
    
    # SQLite doesn't support ALTER COLUMN, so we'll leave it nullable for now
    # The application code will ensure it's always populated


def downgrade() -> None:
    # Remove the model_used column
    op.drop_column('sentiment_data', 'model_used')
