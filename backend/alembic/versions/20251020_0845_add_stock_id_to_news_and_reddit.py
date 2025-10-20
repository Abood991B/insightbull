"""
add stock_id to news_articles and reddit_posts

Revision ID: 20251020_0845_add_stock_id_to_news_and_reddit
Revises: 44d15694e686
Create Date: 2025-10-20 08:45:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251020_0845_add_stock_id_to_news_and_reddit'
down_revision = '44d15694e686'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name if bind is not None else 'sqlite'

    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('news_articles') as batch_op:
        batch_op.add_column(sa.Column('stock_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        # Create index
        batch_op.create_index('ix_news_articles_stock_id', ['stock_id'], unique=False)
        # Create FK inside batch (works via table recreate on SQLite)
        batch_op.create_foreign_key('fk_news_articles_stock', 'stocks_watchlist', ['stock_id'], ['id'])

    with op.batch_alter_table('reddit_posts') as batch_op:
        batch_op.add_column(sa.Column('stock_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        batch_op.create_index('ix_reddit_posts_stock_id', ['stock_id'], unique=False)
        batch_op.create_foreign_key('fk_reddit_posts_stock', 'stocks_watchlist', ['stock_id'], ['id'])


def downgrade() -> None:
    with op.batch_alter_table('reddit_posts') as batch_op:
        batch_op.drop_index('ix_reddit_posts_stock_id')
        batch_op.drop_constraint('fk_reddit_posts_stock', type_='foreignkey')
        batch_op.drop_column('stock_id')

    with op.batch_alter_table('news_articles') as batch_op:
        batch_op.drop_index('ix_news_articles_stock_id')
        batch_op.drop_constraint('fk_news_articles_stock', type_='foreignkey')
        batch_op.drop_column('stock_id')


