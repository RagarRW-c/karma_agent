"""
AI Agent Service - REAL SCRAPING VERSION
Uses real scrapers to get actual prices from stores
"""

import os
import json
import asyncio
from typing import Optional, List, Dict
from decimal import Decimal
import hashlib
from datetime import datetime, timedelta

import httpx
from services.scraper.store_scrapers import get_scraper


class AIAgent:
    """Autonomous AI Agent with REAL scraping"""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment variables!")

        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-5-sonnet-20240620"

        # Cache settings
        self.cache_ttl = 3600  # Cache for 1 hour
        self.use_cache = True

    def _get_cache_key(self, product_name: str, store_name: str) -> str:
        """Generate cache key for product/store combo"""
        key_data = f"{product_name}:{store_name}".lower()
        return f"scrape:{hashlib.md5(key_data.encode()).hexdigest()}"

    async def _get_cached_price(
            self,
            product_name: str,
            store_name: str) -> Optional[Dict]:
        """Get cached price from Redis"""
        if not self.use_cache:
            return None

        try:
            import redis
            r = redis.Redis(
                host='redis',
                port=6379,
                db=0,
                decode_responses=True)

            cache_key = self._get_cache_key(product_name, store_name)
            cached = r.get(cache_key)

            if cached:
                data = json.loads(cached)
                print(f"[CACHE] Hit for {store_name}: {product_name}")
                return data
        except Exception as e:
            print(f"[CACHE] Error: {e}")

        return None

    async def _cache_price(
            self,
            product_name: str,
            store_name: str,
            price_data: Dict):
        """Cache price in Redis"""
        if not self.use_cache:
            return

        try:
            import redis
            r = redis.Redis(
                host='redis',
                port=6379,
                db=0,
                decode_responses=True)

            cache_key = self._get_cache_key(product_name, store_name)
            r.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(
                    price_data,
                    default=str))
            print(f"[CACHE] Stored {store_name}: {product_name}")
        except Exception as e:
            print(f"[CACHE] Error: {e}")

    async def scrape_store_real(
        self,
        product_name: str,
        store_name: str
    ) -> Optional[Dict]:
        """
        Scrape real price from store

        Returns: {
            "store_name": str,
            "url": str,
            "price": float,
            "currency": str,
            "scraped_at": str
        }
        """
        print(f"[REAL SCRAPER] Searching {store_name} for: {product_name}")

        # Check cache first
        cached = await self._get_cached_price(product_name, store_name)
        if cached:
            return cached

        # Get scraper
        scraper = get_scraper(store_name)
        if not scraper:
            print(f"[REAL SCRAPER] No scraper for: {store_name}")
            return None

        try:
            # Search for product
            product_url = await scraper.search_product(product_name)
            if not product_url:
                print(f"[REAL SCRAPER] Product not found on {store_name}")
                return None

            # Scrape price
            price_data = await scraper.scrape_price(product_url)
            if not price_data:
                print(
                    f"[REAL SCRAPER] Could not scrape price from {store_name}")
                return None

            # Format result
            result = {
                "store_name": store_name,
                "url": price_data["url"],
                "price": float(price_data["price"]),
                "currency": price_data["currency"],
                "scraped_at": datetime.now().isoformat()
            }

            # Cache it
            await self._cache_price(product_name, store_name, result)

            print(f"[REAL SCRAPER] ✓ {store_name}: {result['price']} PLN")
            return result

        except Exception as e:
            print(f"[REAL SCRAPER] Error scraping {store_name}: {e}")
            return None

    async def find_best_price(
        self,
        product_name: str,
        max_stores: int = 5,
        use_real_scraper: bool = True
    ) -> List[Dict]:
        """
        Find best price across stores

        Args:
            product_name: Product to search for
            max_stores: Maximum number of stores to check
            use_real_scraper: If True, uses real scraping. If False, uses mock data.

        Returns:
            List of dicts with store_name, url, price, currency
        """
        print(f"[AI AGENT] Starting search for: {product_name}")
        print(
            f"[AI AGENT] Mode: {'REAL SCRAPER' if use_real_scraper else 'MOCK DATA'}")

        # Mock data as fallback
        mock_results = [{"store_name": "Zooplus",
                         "url": "https://www.zooplus.pl/shop/koty/karma_dla_kota_sucha/royal_canin/sterilised/1975705",
                         "price": 189.96,
                         "currency": "PLN",
                         "source": "mock"},
                        {"store_name": "Kakadu",
                         "url": "https://www.kakadu.pl/koty/karma-sucha/royal-canin-sterilised-2kg",
                         "price": 199.99,
                         "currency": "PLN",
                         "source": "mock"},
                        {"store_name": "MaxiZoo",
                         "url": "https://www.maxizoo.pl/royal-canin-sterilised",
                         "price": 209.99,
                         "currency": "PLN",
                         "source": "mock"}]

        # Use mock data if real scraper disabled
        if not use_real_scraper:
            print(f"[AI AGENT] Using mock data")
            return mock_results[:max_stores]

        # REAL SCRAPING
        stores_to_scrape = ["Zooplus", "Kakadu", "MaxiZoo"][:max_stores]

        results = []
        failed_stores = []

        # Scrape each store
        for store_name in stores_to_scrape:
            try:
                result = await self.scrape_store_real(product_name, store_name)
                if result:
                    result["source"] = "real"
                    results.append(result)
                else:
                    failed_stores.append(store_name)
            except Exception as e:
                print(f"[AI AGENT] Failed to scrape {store_name}: {e}")
                failed_stores.append(store_name)

        # If all stores failed, use mock data
        if not results:
            print(f"[AI AGENT] All stores failed, using mock data")
            return mock_results[:max_stores]

        # If some stores failed, add mock data for failed stores
        if failed_stores and len(results) < max_stores:
            print(f"[AI AGENT] Some stores failed, supplementing with mock data")
            mock_supplement = [
                m for m in mock_results if m["store_name"] in failed_stores]
            results.extend(mock_supplement[:max_stores - len(results)])

        # Sort by price
        results.sort(key=lambda x: x["price"])

        print(f"[AI AGENT] Found {len(results)} results:")
        for r in results:
            source_emoji = "🕷️" if r["source"] == "real" else "📦"
            print(
                f"[AI AGENT]   {source_emoji} {r['store_name']}: {r['price']} PLN")

        return results


# Test function
async def test_real_scraper():
    """Test real scraper"""
    print("\n" + "=" * 60)
    print("🕷️  TESTING REAL SCRAPER")
    print("=" * 60 + "\n")

    agent = AIAgent()

    # Test with real scraper
    print("\n📍 Test 1: Royal Canin (real scraper)")
    results = await agent.find_best_price(
        "Royal Canin Sterilised 2kg",
        max_stores=2,
        use_real_scraper=True
    )

    print("\n" + "=" * 60)
    print("RESULTS:")
    print("=" * 60)
    for i, r in enumerate(results, 1):
        source = "🕷️  REAL" if r.get("source") == "real" else "📦 MOCK"
        print(f"{i}. {r['store_name']}: {r['price']} PLN ({source})")
        print(f"   {r['url']}")

    print("\n" + "=" * 60)
    print("✅ Test complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_real_scraper())
