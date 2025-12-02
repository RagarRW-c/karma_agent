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


class AutoAddRequest(BaseModel):
    product_name: str = Field(..., description="Product name to search and add")
    brand: Optional[str] = Field(None, description="Brand name")
    weight_grams: Optional[int] = Field(None, description="Product weight in grams")
    target_price_pln: float = Field(..., description="Target price for alerts")
    auto_add_to_db: bool = Field(True, description="Automatically add product and shop_products to database")


class AutoAddResponse(BaseModel):
    success: bool
    message: str
    product_id: Optional[int]
    added_shops: int
    prices_found: List[PriceResult]


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


@router.post("/auto-add", response_model=AutoAddResponse)
async def auto_add_product(
    request: AutoAddRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    🚀 Fully Autonomous Product Addition
    
    AI Agent will:
    1. Search for the product across stores
    2. Create Product in database
    3. Create Shop entries (if new)
    4. Create ShopProduct entries with URLs
    5. Add AI-based extraction config (no CSS selectors!)
    6. Immediately scrape initial prices
    
    Everything is automatic - just provide product name!
    """
    agent = AIAgent()
    
    # Step 1: Search for product
    results = await agent.find_best_price(request.product_name, max_stores=5)
    
    if not results:
        return AutoAddResponse(
            success=False,
            message="No stores found with this product",
            product_id=None,
            added_shops=0,
            prices_found=[]
        )
    
    # Step 2: Create product in database
    product = models.Product(
        name=request.product_name,
        brand=request.brand,
        weight_grams=request.weight_grams,
        target_price_pln=request.target_price_pln
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Step 3: Add shops and shop_products
    added_count = 0
    
    for result in results:
        # Check if shop exists
        shop = db.query(models.Shop).filter(
            models.Shop.name == result["store_name"]
        ).first()
        
        if not shop:
            # Create new shop
            shop = models.Shop(
                name=result["store_name"],
                base_url=result["url"].split("/")[0] + "//" + result["url"].split("/")[2],
                country_code="PL"
            )
            db.add(shop)
            db.commit()
            db.refresh(shop)
        
        # Create shop_product with AI extraction config
        shop_product = models.ShopProduct(
            product_id=product.id,
            shop_id=shop.id,
            shop_product_url=result["url"],
            extraction_config={
                "method": "ai_vision",  # Use AI instead of CSS selectors!
                "model": "claude-3-5-sonnet",
                "note": "Automatically configured by AI Agent"
            }
        )
        db.add(shop_product)
        
        # Add initial price snapshot
        snapshot = models.PriceSnapshot(
            product_id=product.id,
            shop_id=shop.id,
            price=result["price"],
            currency=result["currency"]
        )
        db.add(snapshot)
        
        added_count += 1
    
    db.commit()
    
    return AutoAddResponse(
        success=True,
        message=f"Successfully added {request.product_name} with {added_count} shops",
        product_id=product.id,
        added_shops=added_count,
        prices_found=[PriceResult(**r) for r in results]
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
            "multi_store_comparison",
            "auto_product_addition"
        ]
    }
