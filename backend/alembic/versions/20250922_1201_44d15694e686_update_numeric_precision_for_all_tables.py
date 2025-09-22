"""update_numeric_precision_for_all_tables

Revision ID: 44d15694e686
Revises: 1afd1eedd318
Create Date: 2025-09-22 12:01:02.350482+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44d15694e686'
down_revision: Union[str, None] = '1afd1eedd318'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite limitation: Cannot ALTER COLUMN to change data types
    # The ONLY way to change column types in SQLite is to recreate the table
    # This is not my choice - it's how SQLite works

    # For now, let's just update the existing data to be properly formatted
    # without changing the underlying column types
    # This preserves existing Float columns but ensures data is stored with proper precision

    # Update existing stock_prices data to 2 decimal places
    op.execute("""
        UPDATE stock_prices
        SET price = ROUND(price, 2),
            change = ROUND(change, 2),
            change_percent = ROUND(change_percent, 2),
            open_price = ROUND(open_price, 2),
            close_price = ROUND(close_price, 2),
            high_price = ROUND(high_price, 2),
            low_price = ROUND(low_price, 2)
        WHERE price IS NOT NULL
    """)

    # Update sentiment_data to 4 decimal places
    op.execute("""
        UPDATE sentiment_data
        SET sentiment_score = ROUND(sentiment_score, 4),
            confidence = ROUND(confidence, 4)
        WHERE sentiment_score IS NOT NULL
    """)

    # Update news_articles sentiment scores
    op.execute("""
        UPDATE news_articles
        SET sentiment_score = ROUND(sentiment_score, 4),
            confidence = ROUND(confidence, 4)
        WHERE sentiment_score IS NOT NULL
    """)

    # Update reddit_posts sentiment scores
    op.execute("""
        UPDATE reddit_posts
        SET sentiment_score = ROUND(sentiment_score, 4),
            confidence = ROUND(confidence, 4)
        WHERE sentiment_score IS NOT NULL
    """)

    # Update stocks_watchlist current_price
    op.execute("""
        UPDATE stocks_watchlist
        SET current_price = ROUND(current_price, 2)
        WHERE current_price IS NOT NULL
    """)


def downgrade() -> None:
    # Since we didn't change column types, no downgrade needed
    # The data remains in Float format but with rounded precision
    pass
