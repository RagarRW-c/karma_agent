#!/bin/bash
# TIER 1 Installer - Creates all files automatically!
set -e

echo "🚀 Installing TIER 1 Features..."

# Check directory
if [ ! -d "services" ]; then
    echo "❌ Run from karma_agent root!"
    exit 1
fi

# Create alerts directory
mkdir -p services/alerts

# Create telegram_bot.py
cat > services/alerts/telegram_bot.py << 'EOF1'
import os
import httpx
from datetime import datetime

class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    def is_configured(self):
        return bool(self.bot_token and self.chat_id)
    
    async def send_price_drop_alert(self, product_name, shop_name, old_price, new_price, url, discount_percent):
        if not self.is_configured():
            return False
        try:
            message = f"🔥 OBNIŻKA!\n\n📦 {product_name}\n🏪 {shop_name}\n\n💵 {old_price:.2f} → {new_price:.2f} PLN\n📉 -{discount_percent:.1f}%\n\n🔗 {url}"
            api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(api_url, json={"chat_id": self.chat_id, "text": message})
                return response.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM] Error: {e}")
            return False

telegram_bot = TelegramBot()
EOF1

# Create alerts router
cat > services/api/routers/alerts.py << 'EOF2'
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
EOF2

# Create __init__.py
touch services/alerts/__init__.py

# Update main.py
if ! grep -q "from services.api.routers.alerts" services/api/main.py; then
    sed -i '/from services.api.routers.ai_agent/a from services.api.routers.alerts import router as alerts_router' services/api/main.py
    sed -i '/app.include_router(ai_agent_router)/a app.include_router(alerts_router)  # Alerts' services/api/main.py
fi

# Update .env.example
if ! grep -q "TELEGRAM_BOT_TOKEN" .env.example; then
    echo "" >> .env.example
    echo "# Telegram Alerts (Optional)" >> .env.example
    echo "TELEGRAM_BOT_TOKEN=your-bot-token" >> .env.example
    echo "TELEGRAM_CHAT_ID=your-chat-id" >> .env.example
fi

echo "✅ TIER 1 installed!"
echo "Restart: cd infra && docker compose up -d --build"
echo "Test: curl http://localhost:8001/alerts/status"
