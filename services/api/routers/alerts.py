"""Alerts API Router"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
import os

router = APIRouter(prefix="/alerts", tags=["alerts"])


class AlertStatus(BaseModel):
    telegram_configured: bool
    email_configured: bool
    telegram_chat_id: Optional[str]
    alert_email: Optional[str]


@router.get("/status", response_model=AlertStatus)
async def get_alert_status():
    """Check alert configuration"""
    telegram_ok = bool(
        os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))
    email_ok = bool(
        os.getenv("SMTP_USER") and
        os.getenv("SMTP_PASSWORD") and
        os.getenv("ALERT_EMAIL")
    )

    return AlertStatus(
        telegram_configured=telegram_ok,
        email_configured=email_ok,
        telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "Not set"),
        alert_email=os.getenv("ALERT_EMAIL", "Not set")
    )


@router.post("/test")
async def test_alert():
    """Send test alert"""
    from services.alerts.telegram_bot import telegram_bot

    results = {}

    if telegram_bot.is_configured():
        success = await telegram_bot.send_price_drop_alert(
            "Test Product - Royal Canin",
            "Zooplus",
            199.99,
            149.99,
            "https://example.com",
            25.0
        )
        results["telegram"] = "sent" if success else "failed"
    else:
        results["telegram"] = "not_configured"

    return {"status": "success", "results": results}
