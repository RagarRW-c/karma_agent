"""
AI Agent Router - Updated with REAL SCRAPING support
"""

from typing import List, Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from services.ai_agent.agent import AIAgent


router = APIRouter(
    prefix="/ai-agent",
    tags=["ai-agent"],
)


class ProductSearchRequest(BaseModel):
    product_name: str = Field(..., description="Product name to search for")
    max_stores: int = Field(3, ge=1, le=5, description="Maximum number of stores")
    use_real_scraper: bool = Field(
        True,
        description="Use real web scraping (True) or mock data (False)"
    )


class PriceResult(BaseModel):
    store_name: str
    url: str
    price: float
    currency: str
    source: Optional[str] = Field(None, description="'real' or 'mock'")
    scraped_at: Optional[str] = None


class ProductSearchResponse(BaseModel):
    product_name: str
    results: List[PriceResult]
    best_price: Optional[float]
    best_store: Optional[str]
    total_stores_found: int
    scraping_mode: str  # "real" or "mock"


@router.post("/search", response_model=ProductSearchResponse)
async def autonomous_search(request: ProductSearchRequest):
    """
    🕷️ Autonomous AI Product Search with REAL SCRAPING

    The AI Agent will:
    1. Search across multiple Polish pet stores
    2. Use Playwright to scrape REAL prices
    3. Cache results in Redis (1 hour)
    4. Compare and return best prices

    **Modes:**
    - `use_real_scraper=true`: Scrapes actual websites (slower, real data)
    - `use_real_scraper=false`: Uses mock data (faster, for testing)

    **Features:**
    - ✅ Real-time price scraping
    - ✅ Smart caching (avoid hitting stores too often)
    - ✅ Fallback to mock data if scraping fails
    - ✅ Automatic error handling

    **Supported Stores:**
    - Zooplus.pl
    - Kakadu.pl
    - MaxiZoo.pl
    """
    agent = AIAgent()

    # Perform search
    results = await agent.find_best_price(
        request.product_name,
        request.max_stores,
        request.use_real_scraper
    )

    # Find best price
    best_price = None
    best_store = None
    if results:
        best_price = results[0]["price"]
        best_store = results[0]["store_name"]

    # Determine mode
    mode = "real" if request.use_real_scraper else "mock"
    if results and any(r.get("source") == "mock" for r in results):
        mode = "mixed"  # Some real, some mock

    return ProductSearchResponse(
        product_name=request.product_name,
        results=[PriceResult(**r) for r in results],
        best_price=best_price,
        best_store=best_store,
        total_stores_found=len(results),
        scraping_mode=mode
    )


@router.get("/status")
async def agent_status():
    """
    Check if AI Agent is configured properly

    Shows:
    - API key status
    - Model being used
    - Available capabilities
    - Scraping mode available
    """
    import os

    has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))

    return {
        "status": "configured" if has_api_key else "missing_api_key",
        "anthropic_api_key": "present" if has_api_key else "missing",
        "model": "claude-3-5-sonnet-20240620",
        "capabilities": [
            "autonomous_search",
            "ai_price_extraction",
            "multi_store_comparison",
            "real_web_scraping",  # NEW!
            "redis_caching",      # NEW!
        ],
        "scraping_modes": {
            "real": "Scrapes actual websites (slower, real prices)",
            "mock": "Uses mock data (faster, for testing)"
        }
    }


@router.post("/clear-cache")
async def clear_cache():
    """
    🗑️ Clear Price Cache

    Clears cached prices from Redis.
    Use this to force fresh scraping.
    """
    try:
        import redis
        r = redis.Redis(host='redis', port=6379, db=0)

        # Get all scrape cache keys
        keys = r.keys("scrape:*")

        if keys:
            deleted = r.delete(*keys)
            return {
                "status": "success",
                "message": f"Cleared {deleted} cached prices"
            }
        else:
            return {
                "status": "success",
                "message": "No cached prices to clear"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to clear cache: {str(e)}"
        }
