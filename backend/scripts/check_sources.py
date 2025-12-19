"""Quick script to check data sources in database."""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'insight_stock.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# First, check the schema
print('\nSENTIMENT_DATA TABLE SCHEMA:')
print('='*60)
cur.execute("PRAGMA table_info(sentiment_data)")
columns = cur.fetchall()
for col in columns:
    print(f'  {col[1]:<30} {col[2]:<15} nullable={col[3]==0}')

print('\n\nDISTINCT SOURCE IN SENTIMENT_DATA:')
print('='*60)
cur.execute('SELECT DISTINCT source FROM sentiment_data ORDER BY source')
sources = cur.fetchall()
for source in sources:
    cur.execute('SELECT COUNT(*) FROM sentiment_data WHERE source = ?', (source[0],))
    count = cur.fetchone()[0]
    print(f'  {source[0]:<20} - {count:>6} records')

print('\n' + '='*60)
print(f'Total sources: {len(sources)}')

conn.close()
