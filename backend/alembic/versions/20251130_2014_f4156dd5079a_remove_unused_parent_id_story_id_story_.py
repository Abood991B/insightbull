"""Remove unused parent_id story_id story_title from hackernews_posts

Revision ID: f4156dd5079a
Revises: 5940f66efa7e
Create Date: 2025-11-30 20:14:29.402572+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f4156dd5079a'
down_revision: Union[str, None] = '5940f66efa7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove unused columns from hackernews_posts table.
    
    These columns were never read/queried in the application:
    - parent_id: For comment threading (not used)
    - story_id: For comment threading (not used)
    - story_title: Redundant with parent story (always stored as None)
    """
    # SQLite doesn't support DROP COLUMN directly in older versions,
    # but modern SQLite (3.35.0+) does. Using batch mode for compatibility.
    with op.batch_alter_table('hackernews_posts', schema=None) as batch_op:
        batch_op.drop_column('parent_id')
        batch_op.drop_column('story_id')
        batch_op.drop_column('story_title')


def downgrade() -> None:
    """Re-add the removed columns if needed."""
    with op.batch_alter_table('hackernews_posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('story_id', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('story_title', sa.VARCHAR(length=500), nullable=True))
