from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from services.api.db import get_db
from services.api import models
from services.api.schemas import ShopCreate, ShopRead

router = APIRouter(
    prefix="/shops",
    tags=["shops"],
)


@router.get("/", response_model=List[ShopRead])
def list_shops(db: Session = Depends(get_db)):
    shops = db.query(models.Shop).order_by(models.Shop.id).all()
    return shops


@router.post("/", response_model=ShopRead, status_code=status.HTTP_201_CREATED)
def create_shop(payload: ShopCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Shop).filter(models.Shop.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Shop with this name already exists")

    shop = models.Shop(
        name=payload.name,
        base_url=payload.base_url,
        country_code=payload.country_code,
    )
    db.add(shop)
    db.commit()
    db.refresh(shop)
    return shop


@router.get("/{shop_id}", response_model=ShopRead)
def get_shop(shop_id: int, db: Session = Depends(get_db)):
    shop = db.query(models.Shop).filter(models.Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")
    return shop
