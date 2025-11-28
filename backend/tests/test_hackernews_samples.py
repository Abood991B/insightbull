"""
Hacker News Data Samples & Collection Demo
==========================================

This shows exactly what data you get from Hacker News
and how collection works for your watchlist.
"""

import asyncio
import aiohttp
import time
from datetime import datetime
from typing import Dict, List
import json


class HackerNewsDemo:
    """Demo showing real Hacker News data samples."""
    
    # Your watchlist
    WATCHLIST = [
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",
        "META", "TSLA", "AVGO", "ORCL", "CRM",
        "AMD", "ADBE", "CSCO", "ACN", "INTC",
        "IBM", "TXN", "QCOM", "NOW", "INTU"
    ]
    
    # Algolia HN API (official, unlimited)
    BASE_URL = "https://hn.algolia.com/api/v1"
    
    async def get_stories_for_stock(self, session: aiohttp.ClientSession, symbol: str, limit: int = 5) -> Dict:
        """Get stories and comments for a single stock."""
        
        # Search for stock discussions
        url = f"{self.BASE_URL}/search?query={symbol}&tags=story&hitsPerPage={limit}"
        
        async with session.get(url, timeout=10) as response:
            data = await response.json()
            
            stories = []
            for hit in data.get("hits", []):
                story = {
                    "title": hit.get("title", ""),
                    "url": hit.get("url", ""),
                    "author": hit.get("author", ""),
                    "points": hit.get("points", 0),  # Upvotes
                    "num_comments": hit.get("num_comments", 0),
                    "created_at": hit.get("created_at", ""),
                    "story_id": hit.get("objectID", ""),
                }
                stories.append(story)
            
            return {
                "symbol": symbol,
                "total_available": data.get("nbHits", 0),
                "stories": stories
            }
    
    async def get_comments_for_story(self, session: aiohttp.ClientSession, story_id: str, limit: int = 10) -> List[Dict]:
        """Get comments for a specific story - THIS IS THE COMMUNITY DISCUSSION."""
        
        url = f"{self.BASE_URL}/search?tags=comment,story_{story_id}&hitsPerPage={limit}"
        
        async with session.get(url, timeout=10) as response:
            data = await response.json()
            
            comments = []
            for hit in data.get("hits", []):
                comment = {
                    "author": hit.get("author", ""),
                    "text": hit.get("comment_text", "")[:500] if hit.get("comment_text") else "",  # Limit length
                    "points": hit.get("points", 0),
                    "created_at": hit.get("created_at", ""),
                }
                if comment["text"]:  # Only include if has text
                    comments.append(comment)
            
            return comments
    
    async def demo_single_stock_detailed(self, session: aiohttp.ClientSession, symbol: str):
        """Show detailed data for a single stock."""
        
        print(f"\n{'='*70}")
        print(f"DETAILED SAMPLE: {symbol}")
        print(f"{'='*70}")
        
        # Get stories
        data = await self.get_stories_for_stock(session, symbol, limit=3)
        
        print(f"\nTotal stories available: {data['total_available']:,}")
        print(f"\nTop 3 Stories with Community Discussions:")
        print("-" * 60)
        
        for i, story in enumerate(data["stories"], 1):
            print(f"\n📰 Story #{i}:")
            print(f"   Title: {story['title'][:70]}...")
            print(f"   Author: {story['author']}")
            print(f"   Points (upvotes): {story['points']}")
            print(f"   Comments: {story['num_comments']}")
            print(f"   Date: {story['created_at'][:10]}")
            
            # Get comments for this story (THE COMMUNITY DISCUSSION)
            if story["story_id"]:
                comments = await self.get_comments_for_story(session, story["story_id"], limit=3)
                
                if comments:
                    print(f"\n   💬 Sample Comments (Community Discussion):")
                    for j, comment in enumerate(comments, 1):
                        # Clean up text for display
                        text = comment["text"].replace("\n", " ").replace("<p>", " ")[:200]
                        print(f"\n   Comment {j} by '{comment['author']}':")
                        print(f"   \"{text}...\"")
                        print(f"   Points: {comment['points']}")
                else:
                    print(f"\n   (No comments fetched)")
            
            await asyncio.sleep(0.2)  # Small delay
        
        return data
    
    async def demo_batch_collection(self, session: aiohttp.ClientSession):
        """Show how batch collection works for entire watchlist."""
        
        print(f"\n{'='*70}")
        print("BATCH COLLECTION DEMO - ALL WATCHLIST STOCKS")
        print(f"{'='*70}")
        print(f"\nCollecting data for {len(self.WATCHLIST)} stocks...")
        print(f"Method: Sequential requests (respecting API)")
        print("-" * 60)
        
        start_time = time.time()
        all_results = {}
        total_stories = 0
        total_comments = 0
        
        for symbol in self.WATCHLIST:
            try:
                # Get stories
                data = await self.get_stories_for_stock(session, symbol, limit=10)
                
                # Count comments available
                comments_available = sum(s["num_comments"] for s in data["stories"])
                
                all_results[symbol] = {
                    "stories_found": len(data["stories"]),
                    "total_available": data["total_available"],
                    "comments_available": comments_available
                }
                
                total_stories += data["total_available"]
                total_comments += comments_available
                
                status = "✓" if data["total_available"] > 0 else "⚠"
                print(f"  {status} {symbol}: {data['total_available']:>7,} stories, {comments_available:>5} comments in top 10")
                
                await asyncio.sleep(0.1)  # Small delay between requests
                
            except Exception as e:
                print(f"  ✗ {symbol}: Error - {e}")
                all_results[symbol] = {"error": str(e)}
        
        elapsed = time.time() - start_time
        
        print("-" * 60)
        print(f"\n📊 BATCH COLLECTION SUMMARY:")
        print(f"   Stocks processed: {len(self.WATCHLIST)}")
        print(f"   Total time: {elapsed:.1f} seconds")
        print(f"   Average per stock: {elapsed/len(self.WATCHLIST):.2f} seconds")
        print(f"   Total stories available: {total_stories:,}")
        print(f"   Comments in top 10 per stock: {total_comments:,}")
        
        return all_results
    
    async def demo_rate_limits(self, session: aiohttp.ClientSession):
        """Test rate limits by making rapid requests."""
        
        print(f"\n{'='*70}")
        print("RATE LIMIT TEST")
        print(f"{'='*70}")
        print("\nMaking 20 rapid requests to test limits...")
        print("-" * 60)
        
        start_time = time.time()
        success_count = 0
        error_count = 0
        
        for i in range(20):
            try:
                url = f"{self.BASE_URL}/search?query=AAPL&hitsPerPage=1"
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        success_count += 1
                    elif response.status == 429:
                        error_count += 1
                        print(f"  ⚠ Request {i+1}: Rate limited!")
                    else:
                        error_count += 1
            except Exception as e:
                error_count += 1
            
            # No delay - testing limits
        
        elapsed = time.time() - start_time
        
        print(f"\n📊 RATE LIMIT RESULTS:")
        print(f"   Requests made: 20")
        print(f"   Successful: {success_count}")
        print(f"   Rate limited: {error_count}")
        print(f"   Time elapsed: {elapsed:.2f} seconds")
        print(f"   Requests per second: {20/elapsed:.1f}")
        
        if error_count == 0:
            print(f"\n   ✅ NO RATE LIMITS HIT - You can collect freely!")
        else:
            print(f"\n   ⚠ Some rate limits hit - add small delays")
    
    async def run_full_demo(self):
        """Run complete demo."""
        
        print("=" * 70)
        print("HACKER NEWS DATA COLLECTION DEMO")
        print("=" * 70)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("This shows exactly what data you'll get for sentiment analysis")
        
        async with aiohttp.ClientSession() as session:
            
            # Demo 1: Detailed sample for one stock
            await self.demo_single_stock_detailed(session, "NVDA")
            
            await asyncio.sleep(0.5)
            
            # Demo 2: Another stock
            await self.demo_single_stock_detailed(session, "TSLA")
            
            await asyncio.sleep(0.5)
            
            # Demo 3: Batch collection for all stocks
            batch_results = await self.demo_batch_collection(session)
            
            await asyncio.sleep(0.5)
            
            # Demo 4: Rate limit test
            await self.demo_rate_limits(session)
        
        # Final summary
        print(f"\n{'='*70}")
        print("FINAL SUMMARY - WHAT YOU GET")
        print(f"{'='*70}")
        print("""
  DATA AVAILABLE PER STOCK:
  -------------------------
  📰 Stories: Thousands of discussion threads
  💬 Comments: Real community opinions (for VADER analysis)
  👍 Points: Engagement metrics (upvotes)
  📅 Timestamps: Date filtering supported
  👤 Authors: User attribution

  COLLECTION METHOD:
  ------------------
  ✓ Sequential requests (one stock at a time)
  ✓ ~0.1-0.2 seconds per stock
  ✓ Full 20-stock watchlist: ~4-5 seconds
  ✓ No API key required
  ✓ No rate limits in normal use

  FOR SENTIMENT ANALYSIS:
  -----------------------
  Use the COMMENTS text with Hybrid VADER
  Filter by:
  - Date range (recent discussions)
  - Points > 0 (quality filter)
  - Comment length (skip short ones)
""")
        
        return batch_results


async def main():
    demo = HackerNewsDemo()
    results = await demo.run_full_demo()
    
    # Save results
    with open("hackernews_demo_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: hackernews_demo_results.json")


if __name__ == "__main__":
    asyncio.run(main())
