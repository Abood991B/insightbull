"""fix_sentiment_data_remove_duplicate_column

Revision ID: 940328a23c49
Revises: 20251020_0845_add_stock_id_to_news_and_reddit
Create Date: 2025-11-02 22:05:58.875862+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '940328a23c49'
down_revision: Union[str, None] = '20251020_0845_add_stock_id_to_news_and_reddit'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix Issue 1: Remove duplicate confidence_score column from sentiment_data
    # This column was never used (all values are NULL)
    with op.batch_alter_table('sentiment_data', schema=None) as batch_op:
        # Check if column exists before dropping (SQLite compatibility)
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('sentiment_data')]
        
        if 'confidence_score' in columns:
            batch_op.drop_column('confidence_score')
    
    # Fix Issue 2: Make sentiment_label NOT NULL with default value
    # All existing rows already have values, so this is safe
    with op.batch_alter_table('sentiment_data', schema=None) as batch_op:
        batch_op.alter_column('sentiment_label',
                            existing_type=sa.String(20),
                            nullable=False,
                            server_default='Neutral')


def downgrade() -> None:
    # Restore confidence_score column if needed
    with op.batch_alter_table('sentiment_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('confidence_score', sa.Float(), nullable=True))
    
    # Make sentiment_label nullable again
    with op.batch_alter_table('sentiment_data', schema=None) as batch_op:
        batch_op.alter_column('sentiment_label',
                            existing_type=sa.String(20),
                            nullable=True,
                            server_default=None)
