"""
Real Store Scrapers - Scrape actual prices from Polish pet stores
"""

import asyncio
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Page, TimeoutError as PlaywrightTimeoutError
import re
from decimal import Decimal


class StoreScraperBase:
    """Base class for store scrapers"""
    
    def __init__(self, store_name: str):
        self.store_name = store_name
    
    async def scrape_price(self, url: str) -> Optional[Dict]:
        """
        Scrape price from store
        Returns: {"price": Decimal, "currency": str, "available": bool} or None
        """
        raise NotImplementedError("Subclasses must implement scrape_price")
    
    def _extract_price_from_text(self, text: str) -> Optional[Decimal]:
        """Extract price from text like '189,99 zł' or '189.99'"""
        if not text:
            return None
        
        # Remove all non-numeric except comma and dot
        cleaned = re.sub(r'[^\d,.]', '', text)
        
        # Replace comma with dot
        cleaned = cleaned.replace(',', '.')
        
        # Extract first number
        match = re.search(r'\d+\.?\d*', cleaned)
        if match:
            try:
                return Decimal(match.group())
            except:
                return None
        return None


class ZooplusScraper(StoreScraperBase):
    """Scraper for Zooplus.pl"""
    
    def __init__(self):
        super().__init__("Zooplus")
        self.base_url = "https://www.zooplus.pl"
    
    async def search_product(self, product_name: str) -> Optional[str]:
        """Search for product and return first result URL"""
        search_query = product_name.replace(' ', '+')
        search_url = f"{self.base_url}/search?query={search_query}"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(2000)  # Wait for JavaScript
                
                # Try to find first product link
                selectors = [
                    'a.product-link',
                    'a[data-zta="product_link"]',
                    'article a[href*="/shop/"]',
                    '.product-item a',
                ]
                
                for selector in selectors:
                    try:
                        first_link = await page.locator(selector).first
                        if await first_link.count() > 0:
                            href = await first_link.get_attribute('href')
                            if href:
                                if href.startswith('http'):
                                    product_url = href
                                else:
                                    product_url = f"{self.base_url}{href}"
                                
                                await browser.close()
                                print(f"[{self.store_name}] Found product: {product_url}")
                                return product_url
                    except:
                        continue
                
                await browser.close()
                print(f"[{self.store_name}] No product found for: {product_name}")
                return None
                
        except Exception as e:
            print(f"[{self.store_name}] Search error: {e}")
            return None
    
    async def scrape_price(self, url: str) -> Optional[Dict]:
        """Scrape price from Zooplus product page"""
        print(f"[{self.store_name}] Scraping: {url}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Try multiple price selectors (Zooplus changes them often)
                price_selectors = [
                    '[data-zta="productPrice"]',
                    '.price-main',
                    '.product-price',
                    '[class*="price"]',
                    '[data-testid="product-price"]',
                ]
                
                price_text = None
                for selector in price_selectors:
                    try:
                        element = await page.locator(selector).first
                        if await element.count() > 0:
                            price_text = await element.text_content()
                            if price_text and any(c.isdigit() for c in price_text):
                                break
                    except:
                        continue
                
                await browser.close()
                
                if price_text:
                    price = self._extract_price_from_text(price_text)
                    if price:
                        print(f"[{self.store_name}] Found price: {price} PLN")
                        return {
                            "price": price,
                            "currency": "PLN",
                            "available": True,
                            "url": url
                        }
                
                print(f"[{self.store_name}] Could not extract price")
                return None
                
        except Exception as e:
            print(f"[{self.store_name}] Error: {e}")
            return None


class KakaduScraper(StoreScraperBase):
    """Scraper for Kakadu.pl"""
    
    def __init__(self):
        super().__init__("Kakadu")
        self.base_url = "https://www.kakadu.pl"
    
    async def search_product(self, product_name: str) -> Optional[str]:
        """Search for product on Kakadu"""
        search_query = product_name.replace(' ', '+')
        search_url = f"{self.base_url}/szukaj?q={search_query}"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                # Find first product
                selectors = [
                    '.product-item a',
                    'article a[href*="/produkt/"]',
                    '.product-link',
                ]
                
                for selector in selectors:
                    try:
                        first_link = await page.locator(selector).first
                        if await first_link.count() > 0:
                            href = await first_link.get_attribute('href')
                            if href:
                                product_url = f"{self.base_url}{href}" if not href.startswith('http') else href
                                await browser.close()
                                print(f"[{self.store_name}] Found: {product_url}")
                                return product_url
                    except:
                        continue
                
                await browser.close()
                return None
                
        except Exception as e:
            print(f"[{self.store_name}] Search error: {e}")
            return None
    
    async def scrape_price(self, url: str) -> Optional[Dict]:
        """Scrape price from Kakadu"""
        print(f"[{self.store_name}] Scraping: {url}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                price_selectors = [
                    '.product-price',
                    '[class*="price"]',
                    '.price-value',
                ]
                
                for selector in price_selectors:
                    try:
                        element = await page.locator(selector).first
                        if await element.count() > 0:
                            price_text = await element.text_content()
                            if price_text:
                                price = self._extract_price_from_text(price_text)
                                if price:
                                    await browser.close()
                                    print(f"[{self.store_name}] Found price: {price} PLN")
                                    return {
                                        "price": price,
                                        "currency": "PLN",
                                        "available": True,
                                        "url": url
                                    }
                    except:
                        continue
                
                await browser.close()
                return None
                
        except Exception as e:
            print(f"[{self.store_name}] Error: {e}")
            return None


class MaxiZooScraper(StoreScraperBase):
    """Scraper for MaxiZoo.pl"""
    
    def __init__(self):
        super().__init__("MaxiZoo")
        self.base_url = "https://www.maxizoo.pl"
    
    async def search_product(self, product_name: str) -> Optional[str]:
        """Search for product on MaxiZoo"""
        search_query = product_name.replace(' ', '+')
        search_url = f"{self.base_url}/search?text={search_query}"
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                selectors = [
                    '.product-tile a',
                    'a[href*="/p/"]',
                    '.product-item a',
                ]
                
                for selector in selectors:
                    try:
                        first_link = await page.locator(selector).first
                        if await first_link.count() > 0:
                            href = await first_link.get_attribute('href')
                            if href:
                                product_url = f"{self.base_url}{href}" if not href.startswith('http') else href
                                await browser.close()
                                print(f"[{self.store_name}] Found: {product_url}")
                                return product_url
                    except:
                        continue
                
                await browser.close()
                return None
                
        except Exception as e:
            print(f"[{self.store_name}] Search error: {e}")
            return None
    
    async def scrape_price(self, url: str) -> Optional[Dict]:
        """Scrape price from MaxiZoo"""
        print(f"[{self.store_name}] Scraping: {url}")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(2000)
                
                price_selectors = [
                    '.product-price',
                    '[class*="price"]',
                    '.price-value',
                ]
                
                for selector in price_selectors:
                    try:
                        element = await page.locator(selector).first
                        if await element.count() > 0:
                            price_text = await element.text_content()
                            if price_text:
                                price = self._extract_price_from_text(price_text)
                                if price:
                                    await browser.close()
                                    print(f"[{self.store_name}] Found price: {price} PLN")
                                    return {
                                        "price": price,
                                        "currency": "PLN",
                                        "available": True,
                                        "url": url
                                    }
                    except:
                        continue
                
                await browser.close()
                return None
                
        except Exception as e:
            print(f"[{self.store_name}] Error: {e}")
            return None


# Factory to get scraper by store name
def get_scraper(store_name: str) -> Optional[StoreScraperBase]:
    """Get scraper instance by store name"""
    scrapers = {
        "zooplus": ZooplusScraper,
        "kakadu": KakaduScraper,
        "maxizoo": MaxiZooScraper,
    }
    
    scraper_class = scrapers.get(store_name.lower())
    if scraper_class:
        return scraper_class()
    return None
