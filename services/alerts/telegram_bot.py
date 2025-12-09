"""Telegram Alert Service"""
import os
import httpx


class TelegramBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def is_configured(self):
        return bool(self.bot_token and self.chat_id)

    async def send_price_drop_alert(
            self,
            product_name,
            shop_name,
            old_price,
            new_price,
            url,
            discount_percent):
        if not self.is_configured():
            return False
        try:
            message = (
                "🔥 OBNIŻKA!\n\n"
                "📦 {0}\n🏪 {1}\n\n"
                "💵 {2:.2f} → {3:.2f} PLN\n"
                "📉 -{4:.1f}%\n\n🔗 {5}"
            ).format(
                product_name,
                shop_name,
                old_price,
                new_price,
                discount_percent,
                url
            )
            api_url = (
                "https://api.telegram.org/bot{0}/sendMessage"
            ).format(self.bot_token)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    api_url,
                    json={"chat_id": self.chat_id, "text": message}
                )
                return response.status_code == 200
        except Exception as e:
            print("[TELEGRAM] Error: {0}".format(e))
            return False


telegram_bot = TelegramBot()
