from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from .db import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    brand = Column(String(100), nullable=True, index=True)
    weight_grams = Column(Integer, nullable=True)
    target_price_pln = Column(Numeric(10, 2), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    shop_products = relationship("ShopProduct", back_populates="product")
    price_snapshots = relationship("PriceSnapshot", back_populates="product")


class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    base_url = Column(String(255), nullable=True)
    country_code = Column(String(2), nullable=True)  # np. PL, DE

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    shop_products = relationship("ShopProduct", back_populates="shop")
    price_snapshots = relationship("PriceSnapshot", back_populates="shop")


class ShopProduct(Base):
    __tablename__ = "shop_products"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    shop_product_url = Column(String(500), nullable=False)
    extraction_config = Column(JSON, nullable=True)  # selektory, patterny itp.

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    product = relationship("Product", back_populates="shop_products")
    shop = relationship("Shop", back_populates="shop_products")


class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="PLN")

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    product = relationship("Product", back_populates="price_snapshots")
    shop = relationship("Shop", back_populates="price_snapshots")
