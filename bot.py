import requests
import time
import os
from datetime import datetime, timedelta

# ================= CONFIGURACIÓN =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv( "CHAT_ID")

ALERT_PERCENT = 50          # % de subida
MIN_VOLUME = 1_000_000      # volumen mínimo en USD
CHECK_INTERVAL = 300        # cada 5 minutos
RESET_HOURS = 24            # reset de alertas

# =================================================

already_alerted = {}
last_reset = datetime.now()

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

def reset_alerts_if_needed():
    global already_alerted, last_reset
    if datetime.now() - last_reset >= timedelta(hours=RESET_HOURS):
        already_alerted = {}
        last_reset = datetime.now()
        send_telegram("🔄 <b>Reset diario de alertas</b>")

def scan_market():
    page = 1
    while True:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 250,
            "page": page,
            "price_change_percentage": "24h"
        }

        response = requests.get(url, params=params)
        coins = response.json()

        if not coins:
            break

        for coin in coins:
            symbol = coin["symbol"].upper()
            change = coin.get("price_change_percentage_24h")
            volume = coin.get("total_volume", 0)

            if (
                change is not None
                and change >= ALERT_PERCENT
                and volume >= MIN_VOLUME
                and symbol not in already_alerted
            ):
                message = (
                    f"🚀 <b>PUMP DETECTADO</b>\n\n"
                    f"🪙 <b>{coin['name']} ({symbol})</b>\n"
                    f"📈 Subida 24h: <b>{round(change,2)}%</b>\n"
                    f"💰 Precio: ${coin['current_price']}\n"
                    f"📊 Volumen 24h: ${volume:,}\n\n"
                    f"🔗 https://www.coingecko.com/en/coins/{coin['id']}"
                )

                send_telegram(message)
                already_alerted[symbol] = datetime.now()

        page += 1

# ================= LOOP PRINCIPAL =================
send_telegram("🤖 <b>Bot iniciado</b>\nEscaneando el mercado 24/7")

while True:
    try:
        reset_alerts_if_needed()
        scan_market()
        time.sleep(CHECK_INTERVAL)
    except Exception as e:
        send_telegram(f"⚠️ Error detectado:\n{e}")

        time.sleep(60)

