"""Quick database health check script."""
import sqlite3
import os

# Connect to database
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'insight_stock.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("=" * 70)
print("DATABASE HEALTH CHECK")
print("=" * 70)

# Check tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in c.fetchall()]
print(f"\n1. TABLES IN DATABASE: {len(tables)}")
for t in tables:
    try:
        cnt = c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"   {t}: {cnt} rows")
    except Exception as e:
        print(f"   {t}: ERROR - {e}")

# Check watchlist
print("\n2. ACTIVE WATCHLIST")
try:
    rows = c.execute("""
        SELECT s.symbol, s.name 
        FROM stocks_watchlist w 
        JOIN stocks s ON w.stock_id = s.id 
        WHERE w.is_active = 1
    """).fetchall()
    for row in rows:
        print(f"   {row[0]}: {row[1]}")
    print(f"   Total Active: {len(rows)}")
except Exception as e:
    print(f"   ERROR: {e}")

# Check sentiment data if exists
print("\n3. SENTIMENT DATA QUALITY")
try:
    # Total count
    total = c.execute("SELECT COUNT(*) FROM sentiment_data").fetchone()[0]
    print(f"   Total records: {total}")
    
    if total > 0:
        # By source
        print("\n   By Source:")
        for row in c.execute("SELECT source, COUNT(*) FROM sentiment_data GROUP BY source").fetchall():
            print(f"      {row[0]}: {row[1]}")
        
        # By label
        print("\n   By Sentiment Label:")
        for row in c.execute("SELECT sentiment_label, COUNT(*), ROUND(COUNT(*) * 100.0 / ?, 1) as pct FROM sentiment_data GROUP BY sentiment_label", (total,)).fetchall():
            print(f"      {row[0]}: {row[1]} ({row[2]}%)")
        
        # By model
        print("\n   By Model Used:")
        for row in c.execute("SELECT COALESCE(model_used, 'NULL') as model, COUNT(*) FROM sentiment_data GROUP BY model_used").fetchall():
            print(f"      {row[0]}: {row[1]}")
        
        # Confidence stats
        print("\n   Confidence Statistics:")
        row = c.execute("SELECT ROUND(AVG(confidence), 3), ROUND(MIN(confidence), 3), ROUND(MAX(confidence), 3) FROM sentiment_data").fetchone()
        print(f"      Avg: {row[0]}, Min: {row[1]}, Max: {row[2]}")
        
        # Confidence distribution
        print("\n   Confidence Distribution:")
        buckets = [
            ("Low (< 0.5)", 0, 0.5),
            ("Medium (0.5-0.7)", 0.5, 0.7),
            ("Good (0.7-0.85)", 0.7, 0.85),
            ("High (>= 0.85)", 0.85, 1.01)
        ]
        for name, low, high in buckets:
            cnt = c.execute("SELECT COUNT(*) FROM sentiment_data WHERE confidence >= ? AND confidence < ?", (low, high)).fetchone()[0]
            pct = round(cnt * 100.0 / total, 1) if total > 0 else 0
            print(f"      {name}: {cnt} ({pct}%)")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 70)
conn.close()
