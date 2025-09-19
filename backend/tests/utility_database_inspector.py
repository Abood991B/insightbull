#!/usr/bin/env python3
"""
Database Content Inspector
=========================

Check what data is currently stored in the SQLite database.
Shows table contents and data statistics.

Usage:
    python check_database.py
"""

import sqlite3
import os
from datetime import datetime

def check_database_contents():
    """Check what's in the database"""
    db_path = "data/insight_stock.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return
    
    print("🗄️  Database Content Inspector")
    print("=" * 50)
    print(f"Database: {db_path}")
    print(f"File size: {os.path.getsize(db_path):,} bytes")
    print()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   • {table[0]}")
        print()
        
        # Check each table content
        for table_name in [t[0] for t in tables]:
            print(f"📊 Table: {table_name}")
            print("-" * 30)
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            print("Columns:")
            for col in columns:
                print(f"   • {col[1]} ({col[2]})")
            
            # Count records
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            print(f"Records: {count}")
            
            # Show sample data if any exists
            if count > 0:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                sample_data = cursor.fetchall()
                
                print("Sample data:")
                for i, row in enumerate(sample_data, 1):
                    print(f"   Row {i}: {row}")
                    
                # Show latest records by timestamp if available
                timestamp_columns = ['created_at', 'timestamp', 'processed_at', 'last_updated', 'date']
                timestamp_col = None
                for col in columns:
                    if col[1] in timestamp_columns:
                        timestamp_col = col[1]
                        break
                
                if timestamp_col:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} ORDER BY {timestamp_col} DESC LIMIT 2;")
                        latest_data = cursor.fetchall()
                        print(f"Latest records (by {timestamp_col}):")
                        for i, row in enumerate(latest_data, 1):
                            print(f"   Latest {i}: {row}")
                    except:
                        pass  # Skip if timestamp column doesn't exist or has issues
            
            print()
        
        # Check for sentiment data specifically
        print("🧠 Sentiment Analysis Data Check:")
        print("-" * 35)
        
        try:
            cursor.execute("""
                SELECT 
                    stock_symbol,
                    COUNT(*) as record_count,
                    MIN(processed_at) as earliest,
                    MAX(processed_at) as latest
                FROM sentiment_data 
                GROUP BY stock_symbol 
                ORDER BY record_count DESC;
            """)
            sentiment_stats = cursor.fetchall()
            
            if sentiment_stats:
                print("Sentiment data by symbol:")
                for row in sentiment_stats:
                    print(f"   {row[0]}: {row[1]} records ({row[2]} to {row[3]})")
            else:
                print("   No sentiment data found")
        except Exception as e:
            print(f"   Could not analyze sentiment data: {e}")
        
        print()
        
        # Check for recent activity
        print("⏰ Recent Activity Check:")
        print("-" * 25)
        
        recent_tables = ['sentiment_data', 'news_articles', 'reddit_posts', 'stock_prices']
        for table in recent_tables:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM {table} 
                    WHERE datetime(created_at) > datetime('now', '-24 hours')
                """)
                recent_count = cursor.fetchone()[0]
                print(f"   {table}: {recent_count} records in last 24 hours")
            except:
                try:
                    cursor.execute(f"""
                        SELECT COUNT(*) 
                        FROM {table} 
                        WHERE datetime(timestamp) > datetime('now', '-24 hours')
                    """)
                    recent_count = cursor.fetchone()[0]
                    print(f"   {table}: {recent_count} records in last 24 hours")
                except:
                    print(f"   {table}: Could not check recent activity")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")


def check_pipeline_storage():
    """Check if the pipeline actually stores data"""
    print("\n🔍 Pipeline Storage Analysis:")
    print("-" * 30)
    
    # Check if pipeline has storage implementation
    try:
        import sys
        sys.path.append('app')
        
        from app.business.pipeline import DataPipeline
        
        # Check methods
        pipeline_methods = [method for method in dir(DataPipeline) if not method.startswith('_')]
        storage_methods = [method for method in pipeline_methods if 'store' in method.lower()]
        
        print(f"Pipeline methods: {len(pipeline_methods)}")
        print(f"Storage-related methods: {storage_methods}")
        
        # Check if sentiment data gets stored
        print("\nStorage implementation check:")
        print("   • _store_data method: Present" if '_store_data' in dir(DataPipeline) else "   • _store_data method: Missing")
        print("   • _store_sentiment_data method: Present" if '_store_sentiment_data' in dir(DataPipeline) else "   • _store_sentiment_data method: Missing")
        
    except Exception as e:
        print(f"Could not analyze pipeline storage: {e}")


if __name__ == "__main__":
    print("Starting database inspection...\n")
    
    check_database_contents()
    check_pipeline_storage()
    
    print("\n" + "=" * 50)
    print("💡 Summary:")
    print("   • If tables are empty, the scheduler hasn't run yet")
    print("   • Scheduler runs: Daily 6 AM UTC, Hourly 9 AM-4 PM weekdays")
    print("   • You can manually test data collection with the test files")
    print("   • Check 'python main.py' logs to see if data collection is working")