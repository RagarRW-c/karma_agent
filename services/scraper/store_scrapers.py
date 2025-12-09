"""Real Store Scrapers"""

from typing import Optional, Dict
from playwright.async_api import async_playwright
import re
from decimal import Decimal


class StoreScraperBase:
    """Base class for store scrapers"""

    def __init__(self, store_name: str):
        self.store_name = store_name

    async def scrape_price(self, url: str) -> Optional[Dict]:
        """Scrape price from store"""
        raise NotImplementedError("Subclasses must implement scrape_price")

    def _extract_price_from_text(self, text: str) -> Optional[Decimal]:
        """Extract price from text like '189,99 zł' or '189.99'"""
        if not text:
            return None

        cleaned = re.sub(r'[^\d,.]', '', text)
        cleaned = cleaned.replace(',', '.')
        match = re.search(r'\d+\.?\d*', cleaned)
        if match:
            try:
                return Decimal(match.group())
            except Exception:
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
        search_url = "{0}/search?query={1}".format(
            self.base_url, search_query)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(2000)

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
                                    product_url = "{0}{1}".format(
                                        self.base_url, href)

                                await browser.close()
                                print("[{0}] Found: {1}".format(
                                    self.store_name, product_url))
                                return product_url
                    except Exception:
                        continue

                await browser.close()
                print("[{0}] No product found for: {1}".format(
                    self.store_name, product_name))
                return None

        except Exception as e:
            print("[{0}] Search error: {1}".format(self.store_name, e))
            return None

    async def scrape_price(self, url: str) -> Optional[Dict]:
        """Scrape price from Zooplus product page"""
        print("[{0}] Scraping: {1}".format(self.store_name, url))

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(url, timeout=30000)
                await page.wait_for_timeout(2000)

                price_selectors = [
                    '[data-zta="productPrice"]',
                    '.price-main',
                    '.product-price',
                    '[class*="price"]',
                ]

                price_text = None
                for selector in price_selectors:
                    try:
                        element = await page.locator(selector).first
                        if await element.count() > 0:
                            price_text = await element.text_content()
                            if price_text and any(
                                    c.isdigit() for c in price_text):
                                break
                    except Exception:
                        continue

                await browser.close()

                if price_text:
                    price = self._extract_price_from_text(price_text)
                    if price:
                        print("[{0}] Found price: {1} PLN".format(
                            self.store_name, price))
                        return {
                            "price": price,
                            "currency": "PLN",
                            "available": True,
                            "url": url
                        }

                print("[{0}] Could not extract price".format(
                    self.store_name))
                return None

        except Exception as e:
            print("[{0}] Error: {1}".format(self.store_name, e))
            return None


class KakaduScraper(StoreScraperBase):
    """Scraper for Kakadu.pl"""

    def __init__(self):
        super().__init__("Kakadu")
        self.base_url = "https://www.kakadu.pl"

    async def search_product(self, product_name: str) -> Optional[str]:
        """Search for product on Kakadu"""
        search_query = product_name.replace(' ', '+')
        search_url = "{0}/szukaj?q={1}".format(self.base_url, search_query)

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                await page.goto(search_url, timeout=30000)
                await page.wait_for_timeout(2000)

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
                                if not href.startswith('http'):
                                    product_url = "{0}{1}".format(
                                        self.base_url, href)
                                else:
                                    product_url = href
                                await browser.close()
                                print("[{0}] Found: {1}".format(
                                    self.store_name, product_url))
                                return product_url
                    except Exception:
                        continue

                await browser.close()
                return None

        except Exception as e:
            print("[{0}] Search error: {1}".format(self.store_name, e))
            return None

    async def scrape_price(self, url: str) -> Optional[Dict]:
        """Scrape price from Kakadu"""
        print("[{0}] Scraping: {1}".format(self.store_name, url))

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
                                price = self._extract_price_from_text(
                                    price_text)
                                if price:
                                    await browser.close()
                                    print("[{0}] Found price: {1} PLN".format(
                                        self.store_name, price))
                                    return {
                                        "price": price,
                                        "currency": "PLN",
                                        "available": True,
                                        "url": url
                                    }
                    except Exception:
                        continue

                await browser.close()
                return None

        except Exception as e:
            print("[{0}] Error: {1}".format(self.store_name, e))
            return None


def get_scraper(store_name: str) -> Optional[StoreScraperBase]:
    """Get scraper instance by store name"""
    scrapers = {
        "zooplus": ZooplusScraper,
        "kakadu": KakaduScraper,
    }

    scraper_class = scrapers.get(store_name.lower())
    if scraper_class:
        return scraper_class()
    return None
