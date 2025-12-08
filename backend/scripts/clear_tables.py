"""Clear sentiment_data, news_articles, and hackernews_posts tables."""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'insight_stock.db')
print(f"Database path: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"Tables in database: {[t[0] for t in tables]}")

# Clear tables
tables_to_clear = ['sentiment_data', 'news_articles', 'hackernews_posts']

for table in tables_to_clear:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        before = cursor.fetchone()[0]
        cursor.execute(f"DELETE FROM {table}")
        conn.commit()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        after = cursor.fetchone()[0]
        print(f"{table}: {before} -> {after} rows")
    except Exception as e:
        print(f"{table}: Error - {e}")

conn.close()
print("Done!")
