"""AI Agent Service - REAL SCRAPING VERSION"""

import os
import json
import hashlib
from typing import Optional, List, Dict
from datetime import datetime

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
        self.cache_ttl = 3600
        self.use_cache = True

    def _get_cache_key(self, product_name: str, store_name: str) -> str:
        """Generate cache key for product/store combo"""
        key_data = "{0}:{1}".format(product_name, store_name).lower()
        return "scrape:{0}".format(
            hashlib.md5(key_data.encode()).hexdigest())

    async def _get_cached_price(
            self, product_name: str, store_name: str) -> Optional[Dict]:
        """Get cached price from Redis"""
        if not self.use_cache:
            return None

        try:
            import redis
            r = redis.Redis(
                host='redis', port=6379, db=0, decode_responses=True)

            cache_key = self._get_cache_key(product_name, store_name)
            cached = r.get(cache_key)

            if cached:
                data = json.loads(cached)
                print("[CACHE] Hit for {0}: {1}".format(
                    store_name, product_name))
                return data
        except Exception as e:
            print("[CACHE] Error: {0}".format(e))

        return None

    async def _cache_price(
            self, product_name: str, store_name: str, price_data: Dict):
        """Cache price in Redis"""
        if not self.use_cache:
            return

        try:
            import redis
            r = redis.Redis(
                host='redis', port=6379, db=0, decode_responses=True)

            cache_key = self._get_cache_key(product_name, store_name)
            r.setex(cache_key, self.cache_ttl,
                    json.dumps(price_data, default=str))
            print("[CACHE] Stored {0}: {1}".format(store_name, product_name))
        except Exception as e:
            print("[CACHE] Error: {0}".format(e))

    async def scrape_store_real(
        self, product_name: str, store_name: str
    ) -> Optional[Dict]:
        """Scrape real price from store"""
        print("[REAL SCRAPER] Searching {0} for: {1}".format(
            store_name, product_name))

        # Check cache first
        cached = await self._get_cached_price(product_name, store_name)
        if cached:
            return cached

        # Get scraper
        scraper = get_scraper(store_name)
        if not scraper:
            print("[REAL SCRAPER] No scraper for: {0}".format(store_name))
            return None

        try:
            # Search for product
            product_url = await scraper.search_product(product_name)
            if not product_url:
                print("[REAL SCRAPER] Product not found on {0}".format(
                    store_name))
                return None

            # Scrape price
            price_data = await scraper.scrape_price(product_url)
            if not price_data:
                print("[REAL SCRAPER] Could not scrape price from {0}".format(
                    store_name))
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

            print("[REAL SCRAPER] ✓ {0}: {1} PLN".format(
                store_name, result['price']))
            return result

        except Exception as e:
            print("[REAL SCRAPER] Error scraping {0}: {1}".format(
                store_name, e))
            return None

    async def find_best_price(
        self,
        product_name: str,
        max_stores: int = 5,
        use_real_scraper: bool = True
    ) -> List[Dict]:
        """Find best price across stores"""
        print("[AI AGENT] Starting search for: {0}".format(product_name))
        mode = 'REAL SCRAPER' if use_real_scraper else 'MOCK DATA'
        print("[AI AGENT] Mode: {0}".format(mode))

        # Mock data as fallback
        mock_results = [
            {
                "store_name": "Zooplus",
                "url": "https://www.zooplus.pl/shop/royal_canin",
                "price": 189.96,
                "currency": "PLN",
                "source": "mock"
            },
            {
                "store_name": "Kakadu",
                "url": "https://www.kakadu.pl/royal-canin",
                "price": 199.99,
                "currency": "PLN",
                "source": "mock"
            },
            {
                "store_name": "MaxiZoo",
                "url": "https://www.maxizoo.pl/royal-canin",
                "price": 209.99,
                "currency": "PLN",
                "source": "mock"
            }
        ]

        # Use mock data if real scraper disabled
        if not use_real_scraper:
            print("[AI AGENT] Using mock data")
            return mock_results[:max_stores]

        # REAL SCRAPING
        stores_to_scrape = ["Zooplus", "Kakadu", "MaxiZoo"][:max_stores]

        results = []
        failed_stores = []

        # Scrape each store
        for store_name in stores_to_scrape:
            try:
                result = await self.scrape_store_real(
                    product_name, store_name)
                if result:
                    result["source"] = "real"
                    results.append(result)
                else:
                    failed_stores.append(store_name)
            except Exception as e:
                print("[AI AGENT] Failed to scrape {0}: {1}".format(
                    store_name, e))
                failed_stores.append(store_name)

        # If all stores failed, use mock data
        if not results:
            print("[AI AGENT] All stores failed, using mock data")
            return mock_results[:max_stores]

        # If some stores failed, add mock data for failed stores
        if failed_stores and len(results) < max_stores:
            print("[AI AGENT] Some stores failed, using mock supplement")
            mock_supplement = [
                m for m in mock_results if m["store_name"] in failed_stores]
            results.extend(mock_supplement[:max_stores - len(results)])

        # Sort by price
        results.sort(key=lambda x: x["price"])

        print("[AI AGENT] Found {0} results:".format(len(results)))
        for r in results:
            source_emoji = "🕷️" if r["source"] == "real" else "📦"
            print("[AI AGENT]   {0} {1}: {2} PLN".format(
                source_emoji, r['store_name'], r['price']))

        return results
