"""
AI Agent Router - Autonomous Product Search API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from services.api.db import get_db
from services.api import models
from services.ai_agent.agent import AIAgent


router = APIRouter(
    prefix="/ai-agent",
    tags=["ai-agent"],
)


class ProductSearchRequest(BaseModel):
    product_name: str = Field(..., description="Product name to search for")
    brand: Optional[str] = Field(None, description="Brand name (optional)")
    weight_grams: Optional[int] = Field(None, description="Product weight in grams")
    target_price_pln: Optional[float] = Field(None, description="Target price in PLN")
    max_stores: int = Field(5, ge=1, le=10, description="Maximum number of stores to search")


class PriceResult(BaseModel):
    store_name: str
    url: str
    price: float
    currency: str


class ProductSearchResponse(BaseModel):
    product_name: str
    results: List[PriceResult]
    best_price: Optional[float]
    best_store: Optional[str]
    total_stores_found: int


@router.post("/search", response_model=ProductSearchResponse)
async def autonomous_search(request: ProductSearchRequest):
    """
    🤖 Autonomous AI Product Search
    
    AI Agent will:
    1. Search across multiple Polish pet stores
    2. Find the product automatically
    3. Extract prices using AI vision (no CSS selectors needed!)
    4. Compare and return best prices
    
    No manual configuration needed!
    """
    agent = AIAgent()
    
    # Perform autonomous search
    results = await agent.find_best_price(request.product_name, request.max_stores)
    
    # Find best price
    best_price = None
    best_store = None
    if results:
        best_price = results[0]["price"]
        best_store = results[0]["store_name"]
    
    return ProductSearchResponse(
        product_name=request.product_name,
        results=[PriceResult(**r) for r in results],
        best_price=best_price,
        best_store=best_store,
        total_stores_found=len(results)
    )


@router.get("/status")
async def agent_status():
    """Check if AI Agent is configured properly"""
    import os
    
    has_api_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    return {
        "status": "configured" if has_api_key else "missing_api_key",
        "anthropic_api_key": "present" if has_api_key else "missing",
        "model": "claude-3-5-sonnet-20241022",
        "capabilities": [
            "autonomous_search",
            "ai_price_extraction",
            "multi_store_comparison"
        ]
    }
