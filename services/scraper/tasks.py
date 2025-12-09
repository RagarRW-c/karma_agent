import asyncio
from celery import shared_task
from services.api.db import SessionLocal
from services.api import models

from services.scraper.main import scrape_shop_product_once  # async


@shared_task(name="services.scraper.tasks.scrape_shop_product",
             bind=True, acks_late=True, max_retries=3, default_retry_delay=60)
def scrape_shop_product(self, shop_product_id: int):
    try:
        asyncio.run(scrape_shop_product_once(shop_product_id))
    except Exception as exc:
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            raise


@shared_task(name="services.scraper.tasks.scrape_all")
def scrape_all():
    db = SessionLocal()
    try:
        ids = [
            sp.id for sp in db.query(
                models.ShopProduct).order_by(
                models.ShopProduct.id).all()]
    finally:
        db.close()

    for _id in ids:
        scrape_shop_product.delay(_id)
