"""Database health check script."""

import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'insight_stock.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print('='*70)
print('DATABASE HEALTH CHECK')
print('='*70)

# 1. Check sentiment_data quality
print('\n1. SENTIMENT DATA QUALITY')
print('-'*50)
cur.execute('SELECT COUNT(*) FROM sentiment_data')
total = cur.fetchone()[0]
print(f'Total records: {total}')

# Check for empty/null raw_text
cur.execute("SELECT COUNT(*) FROM sentiment_data WHERE raw_text IS NULL OR raw_text = ''")
empty_text = cur.fetchone()[0]
print(f'Empty raw_text: {empty_text}')

# Check for very short text (potential rubbish)
cur.execute('SELECT COUNT(*) FROM sentiment_data WHERE LENGTH(raw_text) < 20')
short_text = cur.fetchone()[0]
print(f'Very short text (<20 chars): {short_text}')

# Check confidence distribution
cur.execute('SELECT MIN(confidence), MAX(confidence), AVG(confidence) FROM sentiment_data')
min_c, max_c, avg_c = cur.fetchone()
print(f'Confidence: min={min_c*100:.1f}%, max={max_c*100:.1f}%, avg={avg_c*100:.1f}%')

# Check below 80%
cur.execute('SELECT COUNT(*) FROM sentiment_data WHERE confidence < 0.80')
below_80 = cur.fetchone()[0]
print(f'Below 80% confidence: {below_80}')

# Check for stock_mentions
cur.execute('SELECT COUNT(*) FROM sentiment_data WHERE stock_mentions IS NULL')
null_mentions = cur.fetchone()[0]
print(f'Missing stock_mentions: {null_mentions}')

# 2. Check for duplicate content
print('\n2. DUPLICATE CHECK')
print('-'*50)
cur.execute('SELECT COUNT(*) FROM sentiment_data')
total = cur.fetchone()[0]
cur.execute('SELECT COUNT(DISTINCT content_hash) FROM sentiment_data')
unique = cur.fetchone()[0]
print(f'Total: {total}, Unique hashes: {unique}, Duplicates: {total - unique}')

# 3. Sample of shortest texts
print('\n3. SHORTEST TEXTS (checking for rubbish)')
print('-'*50)
cur.execute('SELECT LENGTH(raw_text), source, raw_text FROM sentiment_data ORDER BY LENGTH(raw_text) ASC LIMIT 5')
for row in cur.fetchall():
    length, source, text = row
    preview = text[:80] if text else 'NULL'
    print(f'[{length} chars] {source}: {preview}')

# 4. Check for URLs/HTML in raw_text (should be preprocessed out)
print('\n4. PREPROCESSING CHECK (URLs/HTML in text)')
print('-'*50)
cur.execute("SELECT COUNT(*) FROM sentiment_data WHERE raw_text LIKE '%http%' OR raw_text LIKE '%</%'")
with_urls_html = cur.fetchone()[0]
print(f'Records with URLs or HTML tags: {with_urls_html}')

# 5. Check created_at distribution
print('\n5. DATA FRESHNESS')
print('-'*50)
cur.execute('SELECT MIN(created_at), MAX(created_at) FROM sentiment_data')
min_date, max_date = cur.fetchone()
print(f'Oldest: {min_date}')
print(f'Newest: {max_date}')

# 6. Check sentiment label distribution
print('\n6. SENTIMENT DISTRIBUTION')
print('-'*50)
cur.execute('SELECT sentiment_label, COUNT(*) FROM sentiment_data GROUP BY sentiment_label')
for row in cur.fetchall():
    label, count = row
    pct = count / total * 100
    print(f'{label}: {count} ({pct:.1f}%)')

# 7. Check model usage
print('\n7. MODEL USAGE')
print('-'*50)
cur.execute('SELECT model_used, COUNT(*) FROM sentiment_data GROUP BY model_used')
for row in cur.fetchall():
    model, count = row
    pct = count / total * 100
    print(f'{model}: {count} ({pct:.1f}%)')

# 8. Sample random records to verify quality
print('\n8. RANDOM SAMPLE (5 records)')
print('-'*50)
cur.execute('''
    SELECT source, sentiment_label, confidence, stock_mentions, 
           SUBSTR(raw_text, 1, 100) 
    FROM sentiment_data 
    ORDER BY RANDOM() 
    LIMIT 5
''')
for i, row in enumerate(cur.fetchall(), 1):
    source, label, conf, mentions, text = row
    print(f'\n{i}. [{source}] {label} ({conf*100:.0f}%) - Mentions: {mentions}')
    print(f'   Text: {text}...')

conn.close()

print('\n' + '='*70)
print('HEALTH CHECK COMPLETE')
print('='*70)
