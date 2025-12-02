"""
AI Agent Service - Autonomous Product Search & Price Extraction

Uses Claude API to:
1. Search for products across multiple stores
2. Extract prices without CSS selectors
3. Smart product matching
4. Auto-discovery of new stores
"""

import os
import json
import asyncio
from typing import Optional, List, Dict
from decimal import Decimal

import httpx
from playwright.async_api import async_playwright


class AIAgent:
    """Autonomous AI Agent for product search and price extraction"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables!")
        
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"
    
    async def _call_claude(self, prompt: str, system: str = None) -> str:
        """Call Claude API"""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        if system:
            payload["system"] = system
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]
    
    async def search_product_urls(self, product_name: str, max_stores: int = 5) -> List[Dict]:
        """
        Use AI to generate search URLs for popular Polish pet stores
        
        Returns list of dicts with 'store_name' and 'search_url'
        """
        
        system_prompt = """You are an expert at finding cat food products in Polish online stores.
Your task is to generate direct search URLs for popular Polish pet stores."""
        
        prompt = f"""
Generate search URLs for the product: "{product_name}"

For these Polish pet stores (in order of popularity):
1. Zooplus.pl
2. Kakadu.pl  
3. MaxiZoo.pl
4. ZooArt.pl
5. ZooLogiczny.pl

Return ONLY a JSON array with this exact format:
[
  {{"store_name": "Zooplus", "search_url": "https://www.zooplus.pl/search?query=royal+canin+sterilised"}},
  {{"store_name": "Kakadu", "search_url": "https://www.kakadu.pl/szukaj?q=royal+canin+sterilised"}}
]

Rules:
- Return ONLY valid JSON, no other text
- Use actual store URLs and search patterns
- Encode spaces as + or %20
- Limit to {max_stores} stores
"""
        
        response = await self._call_claude(prompt, system_prompt)
        
        # Extract JSON from response
        response = response.strip()
        if response.startswith("```json"):
            response = response.replace("```json", "").replace("```", "").strip()
        
        try:
            stores = json.loads(response)
            return stores[:max_stores]
        except json.JSONDecodeError as e:
            print(f"[AI AGENT] Failed to parse JSON: {e}")
            print(f"[AI AGENT] Response was: {response}")
            return []
    
    async def extract_price_from_screenshot(self, image_base64: str, product_name: str) -> Optional[Dict]:
        """
        Use Claude Vision to extract price from screenshot
        
        Returns dict with 'price' and 'currency' or None
        """
        
        system_prompt = """You are an expert at extracting product prices from e-commerce screenshots.
Your task is to find the main product price on the page."""
        
        prompt = f"""
Look at this screenshot of a product page for: "{product_name}"

Find the main product price (not shipping, not old price, just the current selling price).

Return ONLY a JSON object with this exact format:
{{"price": 89.99, "currency": "PLN", "found": true}}

If you cannot find a price, return:
{{"price": null, "currency": null, "found": false}}

Rules:
- Return ONLY valid JSON, no other text
- Extract numeric price value (e.g., "89,99 zł" → 89.99)
- Replace comma with dot for decimals
- Use PLN for Polish złoty
"""
        
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            response_text = data["content"][0]["text"]
        
        # Extract JSON from response
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        try:
            price_data = json.loads(response_text)
            if price_data.get("found"):
                return {
                    "price": Decimal(str(price_data["price"])),
                    "currency": price_data["currency"]
                }
            return None
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[AI AGENT] Failed to parse price JSON: {e}")
            print(f"[AI AGENT] Response was: {response_text}")
            return None
    
    async def scrape_product_with_ai(self, url: str, product_name: str) -> Optional[Dict]:
        """
        Scrape product page and extract price using AI vision
        
        Returns dict with 'url', 'price', 'currency' or None
        """
        print(f"[AI AGENT] Scraping {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, timeout=30000, wait_until="networkidle")
                
                # Take screenshot
                screenshot_bytes = await page.screenshot(full_page=False)
                screenshot_base64 = screenshot_bytes.hex()  # Convert to hex for base64
                import base64
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                await browser.close()
                
                # Extract price using AI
                price_data = await self.extract_price_from_screenshot(screenshot_base64, product_name)
                
                if price_data:
                    return {
                        "url": url,
                        "price": price_data["price"],
                        "currency": price_data["currency"]
                    }
                
                return None
                
            except Exception as e:
                print(f"[AI AGENT] Error scraping {url}: {e}")
                await browser.close()
                return None
    
    async def find_best_price(self, product_name: str, max_stores: int = 5) -> List[Dict]:
        """
        Autonomous search for best price across multiple stores
        
        Returns list of dicts with 'store_name', 'url', 'price', 'currency'
        
        NOTE: Currently using mock data while Claude API integration is being finalized.
        The architecture supports real AI-powered search - this demonstrates the interface.
        """
        print(f"[AI AGENT] Starting autonomous search for: {product_name}")
        print(f"[AI AGENT] Using mock data for demo (Claude API integration in progress)")
        
        # Mock results with realistic data
        mock_results = [
            {
                "store_name": "Zooplus",
                "url": "https://www.zooplus.pl/shop/koty/karma_dla_kota_sucha/royal_canin/sterilised/1975705",
                "price": 189.96,
                "currency": "PLN"
            },
            {
                "store_name": "Kakadu",
                "url": "https://www.kakadu.pl/koty/karma-sucha/royal-canin-sterilised-2kg",
                "price": 199.99,
                "currency": "PLN"
            },
            {
                "store_name": "MaxiZoo",
                "url": "https://www.maxizoo.pl/royal-canin-sterilised-appetite-control",
                "price": 209.99,
                "currency": "PLN"
            },
            {
                "store_name": "ZooArt",
                "url": "https://www.zooart.com.pl/royal-canin-sterilised",
                "price": 219.99,
                "currency": "PLN"
            },
            {
                "store_name": "ZooLogiczny",
                "url": "https://www.zoologiczny.pl/royal-canin-sterilised-37",
                "price": 229.99,
                "currency": "PLN"
            }
        ]
        
        # Filter by max_stores and sort by price
        results = mock_results[:max_stores]
        results.sort(key=lambda x: x["price"])
        
        print(f"[AI AGENT] Found {len(results)} results")
        for r in results:
            print(f"[AI AGENT] ✓ {r['store_name']}: {r['price']} {r['currency']}")
        
        return results


# Convenience function for testing
async def test_agent():
    """Test the AI Agent"""
    agent = AIAgent()
    
    product_name = "Royal Canin Sterilised 2kg"
    print(f"\n🤖 AI Agent: Searching for '{product_name}'...\n")
    
    results = await agent.find_best_price(product_name, max_stores=3)
    
    print("\n" + "="*60)
    print("RESULTS:")
    print("="*60)
    
    if results:
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['store_name']}: {result['price']} {result['currency']}")
            print(f"   {result['url']}")
    else:
        print("No results found")


if __name__ == "__main__":
    asyncio.run(test_agent())