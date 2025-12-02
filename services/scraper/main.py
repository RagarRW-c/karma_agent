import asyncio
from decimal import Decimal
from typing import Optional

from playwright.async_api import async_playwright
from sqlalchemy.orm import Session

from services.api.db import SessionLocal
from services.api import models


async def _fetch_price_from_page(url: str, selector: str) -> Optional[Decimal]:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, timeout=30000)

        element = await page.query_selector(selector)
        if element is None:
            await browser.close()
            print(f"[SCRAPER] Brak elementu dla selektora: {selector} ({url})")
            return None

        text = await element.inner_text()
        await browser.close()

    cleaned = (
        text.replace("zł", "")
        .replace("PLN", "")
        .replace("\xa0", " ")
        .strip()
    )
    cleaned = cleaned.replace(",", ".")
    numeric_str = "".join(ch for ch in cleaned if ch.isdigit() or ch == ".")

    if not numeric_str:
        print(f"[SCRAPER] Nie udało się wyciągnąć liczby z tekstu ceny: {text!r}")
        return None

    try:
        return Decimal(numeric_str)
    except Exception as exc:
        print(f"[SCRAPER] Błąd parsowania ceny {numeric_str!r}: {exc}")
        return None


async def scrape_shop_product_once(shop_product_id: int) -> None:
    db: Session = SessionLocal()

    try:
        sp = db.query(models.ShopProduct).filter(models.ShopProduct.id == shop_product_id).first()
        if sp is None:
            print(f"[SCRAPER] ShopProduct id={shop_product_id} nie istnieje.")
            return

        if not sp.extraction_config:
            print(f"[SCRAPER] Brak extraction_config dla ShopProduct id={shop_product_id}")
            return

        selector = sp.extraction_config.get("selector_price")
        if not selector:
            print(f"[SCRAPER] Brak 'selector_price' w extraction_config dla id={shop_product_id}")
            return

        url = sp.shop_product_url
        print(f"[SCRAPER] Pobieram cenę: shop_product_id={shop_product_id}, url={url}")

        price = await _fetch_price_from_page(url, selector)
        if price is None:
            print(f"[SCRAPER] Nie udało się pobrać ceny dla id={shop_product_id}")
            return

        snapshot = models.PriceSnapshot(
            product_id=sp.product_id,
            shop_id=sp.shop_id,
            price=price,
            currency="PLN",
        )
        db.add(snapshot)
        db.commit()

        print(
            f"[SCRAPER] Zapisano price_snapshot: product_id={sp.product_id}, shop_id={sp.shop_id}, price={price}"
        )
    finally:
        db.close()


async def scrape_all_shop_products_once() -> None:
    db: Session = SessionLocal()
    try:
        all_sp = db.query(models.ShopProduct).order_by(models.ShopProduct.id).all()
        ids = [sp.id for sp in all_sp]
    finally:
        db.close()

    print(f"[SCRAPER] Znaleziono {len(ids)} wpisów w shop_products.")

    for sp_id in ids:
        try:
            await scrape_shop_product_once(sp_id)
        except Exception as exc:
            print(f"[SCRAPER] Błąd przy scrapowaniu shop_product_id={sp_id}: {exc}")


def main():
    asyncio.run(scrape_all_shop_products_once())


if __name__ == "__main__":
    main()
