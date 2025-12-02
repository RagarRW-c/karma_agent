#!/usr/bin/env python3
"""
Skrypt do inicjalizacji przykładowych danych w bazie.
Użycie: python init_sample_data.py
"""

import os
import sys
from sqlalchemy.orm import Session

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api.db import SessionLocal
from services.api import models


def create_sample_data():
    db: Session = SessionLocal()
    
    try:
        print("🚀 Inicjalizacja przykładowych danych...")
        
        # Sprawdź czy dane już istnieją
        existing_products = db.query(models.Product).count()
        if existing_products > 0:
            print(f"⚠️  Baza już zawiera {existing_products} produktów. Pomijam inicjalizację.")
            return
        
        # 1. Dodaj sklepy
        print("\n📦 Tworzenie sklepów...")
        
        shops_data = [
            {
                "name": "Zooplus",
                "base_url": "https://www.zooplus.pl",
                "country_code": "PL"
            },
            {
                "name": "Kakadu",
                "base_url": "https://www.kakadu.pl",
                "country_code": "PL"
            },
            {
                "name": "Maxi Zoo",
                "base_url": "https://www.maxizoo.pl",
                "country_code": "PL"
            }
        ]
        
        shops = []
        for shop_data in shops_data:
            shop = models.Shop(**shop_data)
            db.add(shop)
            shops.append(shop)
            print(f"  ✓ {shop_data['name']}")
        
        db.commit()
        
        # 2. Dodaj produkty
        print("\n🐱 Tworzenie produktów...")
        
        products_data = [
            {
                "name": "Royal Canin Sterilised 37",
                "brand": "Royal Canin",
                "weight_grams": 2000,
                "target_price_pln": 89.99
            },
            {
                "name": "Whiskas Adult Kurczak",
                "brand": "Whiskas",
                "weight_grams": 1400,
                "target_price_pln": 29.99
            },
            {
                "name": "Felix Senior",
                "brand": "Felix",
                "weight_grams": 340,
                "target_price_pln": 4.99
            },
            {
                "name": "Perfect Fit Indoor",
                "brand": "Perfect Fit",
                "weight_grams": 1400,
                "target_price_pln": 35.99
            }
        ]
        
        products = []
        for product_data in products_data:
            product = models.Product(**product_data)
            db.add(product)
            products.append(product)
            print(f"  ✓ {product_data['brand']} {product_data['name']}")
        
        db.commit()
        
        # 3. Dodaj przykładowe shop_products (bez URL - musisz je dodać ręcznie)
        print("\n🔗 Tworzenie połączeń produkt-sklep...")
        print("⚠️  UWAGA: URLe i selektory musisz dodać ręcznie przez API!")
        print("    Przykład: POST /shop-products z odpowiednimi danymi\n")
        
        # Przykładowe połączenia (bez URL i extraction_config)
        for product in products:
            for shop in shops[:2]:  # Tylko 2 pierwsze sklepy dla przykładu
                shop_product = models.ShopProduct(
                    product_id=product.id,
                    shop_id=shop.id,
                    shop_product_url=f"https://example.com/product/{product.id}",  # Placeholder
                    extraction_config={
                        "selector_price": ".price",  # Placeholder - wymaga dostosowania!
                        "note": "To jest przykładowy selector - musisz go dostosować do konkretnej strony!"
                    }
                )
                db.add(shop_product)
                print(f"  ✓ {product.name} @ {shop.name}")
        
        db.commit()
        
        print("\n✅ Inicjalizacja zakończona!")
        print("\n📋 Kolejne kroki:")
        print("  1. Zaktualizuj shop_products przez API z prawdziwymi URLami")
        print("  2. Dostosuj CSS selektory w extraction_config")
        print("  3. Uruchom scraper: docker exec -it karma_scraper python -m services.scraper.main")
        print("  4. Otwórz dashboard: http://localhost:8000/")
        
        print("\n📊 Statystyki:")
        print(f"  - Sklepy: {db.query(models.Shop).count()}")
        print(f"  - Produkty: {db.query(models.Product).count()}")
        print(f"  - Połączenia: {db.query(models.ShopProduct).count()}")
        
    except Exception as e:
        print(f"\n❌ Błąd podczas inicjalizacji: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_sample_data()
