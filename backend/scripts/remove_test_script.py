"""Remove test_script entries from sentiment_data."""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'insight_stock.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print('\nREMOVING TEST_SCRIPT ENTRIES FROM SENTIMENT_DATA')
print('='*60)

# Check what we're about to delete
cur.execute("SELECT id, stock_id, sentiment_label, created_at FROM sentiment_data WHERE source = 'test_script'")
records = cur.fetchall()
print(f'\nFound {len(records)} test_script record(s):')
for rec in records:
    print(f'  ID: {rec[0]}, Stock: {rec[1]}, Sentiment: {rec[2]}, Created: {rec[3]}')

# Delete the records
cur.execute("DELETE FROM sentiment_data WHERE source = 'test_script'")
deleted = cur.rowcount
conn.commit()

print(f'\n✓ Deleted {deleted} test_script record(s)')

# Verify
cur.execute("SELECT COUNT(*) FROM sentiment_data WHERE source = 'test_script'")
remaining = cur.fetchone()[0]
print(f'  Remaining test_script records: {remaining}')

print('\n' + '='*60)
print('CLEANUP COMPLETE\n')

conn.close()
