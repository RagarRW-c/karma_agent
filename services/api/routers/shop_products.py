from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.api.db import get_db
from services.api import models
from services.api.schemas import ShopProductCreate, ShopProductRead

router = APIRouter(
    prefix="/shop-products",
    tags=["shop-products"],
)


@router.get("/", response_model=List[ShopProductRead])
def list_shop_products(db: Session = Depends(get_db)):
    items = db.query(models.ShopProduct).order_by(models.ShopProduct.id).all()
    return items


@router.post("/", response_model=ShopProductRead, status_code=status.HTTP_201_CREATED)
def create_shop_product(payload: ShopProductCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=400, detail="Product does not exist")

    shop = db.query(models.Shop).filter(models.Shop.id == payload.shop_id).first()
    if not shop:
        raise HTTPException(status_code=400, detail="Shop does not exist")

    item = models.ShopProduct(
        product_id=payload.product_id,
        shop_id=payload.shop_id,
        shop_product_url=payload.shop_product_url,
        extraction_config=payload.extraction_config,
    )

    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{shop_product_id}", response_model=ShopProductRead)
def get_shop_product(shop_product_id: int, db: Session = Depends(get_db)):
    item = db.query(models.ShopProduct).filter(models.ShopProduct.id == shop_product_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="ShopProduct not found")
    return item
