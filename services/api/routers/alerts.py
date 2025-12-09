from fastapi import APIRouter
from pydantic import BaseModel
import os

router = APIRouter(prefix="/alerts", tags=["alerts"])

class AlertStatus(BaseModel):
    telegram_configured: bool

@router.get("/status")
async def get_alert_status():
    telegram_ok = bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
    return {"telegram_configured": telegram_ok}

@router.post("/test")
async def test_alert():
    from services.alerts.telegram_bot import telegram_bot
    if telegram_bot.is_configured():
        success = await telegram_bot.send_price_drop_alert("Test", "Shop", 199.99, 149.99, "https://test.com", 25.0)
        return {"status": "sent" if success else "failed"}
    return {"status": "not_configured"}
