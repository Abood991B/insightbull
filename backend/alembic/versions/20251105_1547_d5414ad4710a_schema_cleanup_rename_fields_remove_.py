"""schema_cleanup_rename_fields_remove_redundant

Revision ID: d5414ad4710a
Revises: 940328a23c49
Create Date: 2025-11-05 15:47:01.569609+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd5414ad4710a'
down_revision: Union[str, None] = '940328a23c49'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL for SQLite to avoid foreign key reflection issues
    conn = op.get_bind()
    
    # 1. Rename extra_data to additional_metadata in sentiment_data
    conn.execute(sa.text("ALTER TABLE sentiment_data RENAME COLUMN extra_data TO additional_metadata"))
    
    # 2. Rename timestamp to price_timestamp in stock_prices  
    conn.execute(sa.text("ALTER TABLE stock_prices RENAME COLUMN timestamp TO price_timestamp"))
    
    # 3. Create new stock_prices table without created_at
    conn.execute(sa.text("""
        CREATE TABLE stock_prices_new (
            id TEXT PRIMARY KEY,
            stock_id TEXT NOT NULL,
            symbol TEXT,
            name TEXT,
            price NUMERIC(10, 2) NOT NULL,
            volume INTEGER,
            change NUMERIC(8, 2),
            change_percent NUMERIC(6, 2),
            price_timestamp DATETIME NOT NULL,
            open_price NUMERIC(10, 2),
            close_price NUMERIC(10, 2),
            high_price NUMERIC(10, 2),
            low_price NUMERIC(10, 2),
            FOREIGN KEY (stock_id) REFERENCES stocks_watchlist(id)
        )
    """))
    
    # Copy data
    conn.execute(sa.text("""
        INSERT INTO stock_prices_new SELECT id, stock_id, symbol, name, price, volume, change, change_percent, price_timestamp, open_price, close_price, high_price, low_price FROM stock_prices
    """))
    
    # Drop old and rename new
    conn.execute(sa.text("DROP TABLE stock_prices"))
    conn.execute(sa.text("ALTER TABLE stock_prices_new RENAME TO stock_prices"))
    
    # 4. Create new news_articles table without created_at
    conn.execute(sa.text("""
        CREATE TABLE news_articles_new (
            id TEXT PRIMARY KEY,
            stock_id TEXT,
            title TEXT NOT NULL,
            content TEXT,
            url TEXT UNIQUE,
            source TEXT NOT NULL,
            author TEXT,
            published_at DATETIME NOT NULL,
            sentiment_score NUMERIC(5, 4),
            confidence NUMERIC(5, 4),
            stock_mentions JSON,
            FOREIGN KEY (stock_id) REFERENCES stocks_watchlist(id)
        )
    """))
    
    conn.execute(sa.text("""
        INSERT INTO news_articles_new SELECT id, stock_id, title, content, url, source, author, published_at, sentiment_score, confidence, stock_mentions FROM news_articles
    """))
    
    conn.execute(sa.text("DROP TABLE news_articles"))
    conn.execute(sa.text("ALTER TABLE news_articles_new RENAME TO news_articles"))
    
    # 5. Create new reddit_posts table without created_at
    conn.execute(sa.text("""
        CREATE TABLE reddit_posts_new (
            id TEXT PRIMARY KEY,
            stock_id TEXT,
            reddit_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            subreddit TEXT NOT NULL,
            author TEXT,
            score INTEGER DEFAULT 0,
            num_comments INTEGER DEFAULT 0,
            url TEXT,
            created_utc DATETIME NOT NULL,
            sentiment_score NUMERIC(5, 4),
            confidence NUMERIC(5, 4),
            stock_mentions JSON,
            FOREIGN KEY (stock_id) REFERENCES stocks_watchlist(id)
        )
    """))
    
    conn.execute(sa.text("""
        INSERT INTO reddit_posts_new SELECT id, stock_id, reddit_id, title, content, subreddit, author, score, num_comments, url, created_utc, sentiment_score, confidence, stock_mentions FROM reddit_posts
    """))
    
    conn.execute(sa.text("DROP TABLE reddit_posts"))
    conn.execute(sa.text("ALTER TABLE reddit_posts_new RENAME TO reddit_posts"))


def downgrade() -> None:
    # Reverse the changes
    
    # 1. Add back created_at columns
    with op.batch_alter_table('reddit_posts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    
    with op.batch_alter_table('news_articles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    
    with op.batch_alter_table('stock_prices', schema=None) as batch_op:
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()))
    
    # 2. Rename price_timestamp back to timestamp
    with op.batch_alter_table('stock_prices', schema=None) as batch_op:
        batch_op.alter_column('price_timestamp', new_column_name='timestamp')
    
    # 3. Rename additional_metadata back to extra_data
    with op.batch_alter_table('sentiment_data', schema=None) as batch_op:
        batch_op.alter_column('additional_metadata', new_column_name='extra_data')
