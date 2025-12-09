from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from services.api.db import get_db
from services.api import models
from services.api.schemas import PriceSnapshotRead, ProductWithCurrentPrice, BestDeal

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
)


@router.get("/price-history/{product_id}", response_model=List[PriceSnapshotRead])
def get_price_history(
    product_id: int,
    shop_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Pobiera historię cen dla danego produktu.
    Opcjonalnie można filtrować po sklepie i okresie czasu.
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    date_from = datetime.utcnow() - timedelta(days=days)

    query = db.query(models.PriceSnapshot).filter(
        models.PriceSnapshot.product_id == product_id,
        models.PriceSnapshot.created_at >= date_from
    )

    if shop_id:
        query = query.filter(models.PriceSnapshot.shop_id == shop_id)

    snapshots = query.order_by(models.PriceSnapshot.created_at).all()
    return snapshots


@router.get("/current-prices", response_model=List[ProductWithCurrentPrice])
def get_current_prices(db: Session = Depends(get_db)):
    """
    Zwraca listę wszystkich produktów z ich najnowszymi cenami ze wszystkich sklepów.
    """
    products = db.query(models.Product).all()
    result = []

    for product in products:
        # Pobierz najnowszą cenę dla każdego sklepu
        latest_prices = (
            db.query(
                models.PriceSnapshot.shop_id,
                models.Shop.name.label("shop_name"),
                models.PriceSnapshot.price,
                models.PriceSnapshot.currency,
                models.PriceSnapshot.created_at
            )
            .join(models.Shop)
            .filter(models.PriceSnapshot.product_id == product.id)
            .order_by(models.PriceSnapshot.shop_id, desc(models.PriceSnapshot.created_at))
            .distinct(models.PriceSnapshot.shop_id)
            .all()
        )

        prices = [
            {
                "shop_id": p.shop_id,
                "shop_name": p.shop_name,
                "price": float(p.price),
                "currency": p.currency,
                "updated_at": p.created_at
            }
            for p in latest_prices
        ]

        # Znajdź najniższą cenę
        min_price = min([p["price"] for p in prices]) if prices else None

        result.append({
            "id": product.id,
            "name": product.name,
            "brand": product.brand,
            "weight_grams": product.weight_grams,
            "target_price_pln": float(product.target_price_pln) if product.target_price_pln else None,
            "prices": prices,
            "min_price": min_price,
            "price_count": len(prices)
        })

    return result


@router.get("/best-deals", response_model=List[BestDeal])
def get_best_deals(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Zwraca najlepsze oferty - produkty poniżej ceny docelowej lub z największym spadkiem cen.
    """
    products = db.query(models.Product).filter(models.Product.target_price_pln.isnot(None)).all()
    deals = []

    for product in products:
        # Pobierz najnowszą najniższą cenę
        latest_price = (
            db.query(models.PriceSnapshot)
            .filter(models.PriceSnapshot.product_id == product.id)
            .order_by(desc(models.PriceSnapshot.created_at))
            .first()
        )

        if not latest_price:
            continue

        current_price = float(latest_price.price)
        target_price = float(product.target_price_pln)

        if current_price <= target_price:
            shop = db.query(models.Shop).filter(models.Shop.id == latest_price.shop_id).first()
            discount_percent = ((target_price - current_price) / target_price) * 100

            deals.append({
                "product_id": product.id,
                "product_name": product.name,
                "brand": product.brand,
                "shop_id": latest_price.shop_id,
                "shop_name": shop.name if shop else "Unknown",
                "current_price": current_price,
                "target_price": target_price,
                "discount_percent": round(discount_percent, 2),
                "updated_at": latest_price.created_at
            })

    # Sortuj po największym rabacie
    deals.sort(key=lambda x: x["discount_percent"], reverse=True)
    return deals[:limit]


@router.get("/price-trends/{product_id}")
def get_price_trends(
    product_id: int,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Analiza trendu cenowego dla produktu.
    Zwraca średnią cenę, minimalną, maksymalną i trend (rosnący/malejący).
    """
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    date_from = datetime.utcnow() - timedelta(days=days)

    snapshots = (
        db.query(models.PriceSnapshot)
        .filter(
            models.PriceSnapshot.product_id == product_id,
            models.PriceSnapshot.created_at >= date_from
        )
        .order_by(models.PriceSnapshot.created_at)
        .all()
    )

    if not snapshots:
        raise HTTPException(status_code=404, detail="No price data available")

    prices = [float(s.price) for s in snapshots]
    avg_price = sum(prices) / len(prices)
    min_price = min(prices)
    max_price = max(prices)

    # Prosty trend - porównanie pierwszych i ostatnich 3 dni
    first_week = prices[:len(prices)//3] if len(prices) > 9 else prices[:3]
    last_week = prices[-len(prices)//3:] if len(prices) > 9 else prices[-3:]

    avg_first = sum(first_week) / len(first_week)
    avg_last = sum(last_week) / len(last_week)

    if avg_last < avg_first * 0.95:
        trend = "falling"
    elif avg_last > avg_first * 1.05:
        trend = "rising"
    else:
        trend = "stable"

    return {
        "product_id": product_id,
        "product_name": product.name,
        "period_days": days,
        "data_points": len(snapshots),
        "average_price": round(avg_price, 2),
        "min_price": round(min_price, 2),
        "max_price": round(max_price, 2),
        "trend": trend,
        "price_change_percent": round(((avg_last - avg_first) / avg_first) * 100, 2)
    }
