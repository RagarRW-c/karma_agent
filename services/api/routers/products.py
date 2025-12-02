from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.api.db import get_db
from services.api import models
from services.api.schemas import ProductCreate, ProductRead

router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=List[ProductRead])
def list_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).order_by(models.Product.id).all()
    return products


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(
        name=payload.name,
        brand=payload.brand,
        weight_grams=payload.weight_grams,
        target_price_pln=payload.target_price_pln,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
