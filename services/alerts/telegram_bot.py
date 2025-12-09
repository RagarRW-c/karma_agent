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
