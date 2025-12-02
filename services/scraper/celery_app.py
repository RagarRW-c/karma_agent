import os
from celery import Celery

BROKER = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", BROKER)

app = Celery("karma_scraper", broker=BROKER, backend=BACKEND)

app.conf.task_serializer = "json"
app.conf.result_serializer = "json"
app.conf.accept_content = ["json"]

try:
    interval_min = int(os.getenv("SCRAPE_INTERVAL_MIN", "30"))
except Exception:
    interval_min = 30

app.conf.beat_schedule = {
    "schedule-scrape-all-every-n-minutes": {
        "task": "services.scraper.tasks.scrape_all",
        "schedule": interval_min * 60,
    }
}

# CLI compatibility
celery = app
