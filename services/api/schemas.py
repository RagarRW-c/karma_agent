from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ---------- PRODUCT ----------

class ProductBase(BaseModel):
    name: str = Field(..., max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    weight_grams: Optional[int] = None
    target_price_pln: Optional[float] = None


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- SHOP ----------

class ShopBase(BaseModel):
    name: str = Field(..., max_length=100)
    base_url: Optional[str] = Field(None, max_length=255)
    country_code: Optional[str] = Field(None, max_length=2)


class ShopCreate(ShopBase):
    pass


class ShopRead(ShopBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- SHOP PRODUCT ----------

class ShopProductBase(BaseModel):
    product_id: int
    shop_id: int
    shop_product_url: str
    extraction_config: Optional[dict] = None


class ShopProductCreate(ShopProductBase):
    pass


class ShopProductRead(ShopProductBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- PRICE SNAPSHOT ----------

class PriceSnapshotRead(BaseModel):
    id: int
    product_id: int
    shop_id: int
    price: float
    currency: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- ANALYTICS ----------

class ShopPrice(BaseModel):
    shop_id: int
    shop_name: str
    price: float
    currency: str
    updated_at: datetime


class ProductWithCurrentPrice(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    weight_grams: Optional[int]
    target_price_pln: Optional[float]
    prices: List[ShopPrice]
    min_price: Optional[float]
    price_count: int


class BestDeal(BaseModel):
    product_id: int
    product_name: str
    brand: Optional[str]
    shop_id: int
    shop_name: str
    current_price: float
    target_price: float
    discount_percent: float
    updated_at: datetime
