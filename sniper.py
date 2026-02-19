import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# ==========================
# CONFIG
# ==========================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

MAX_PRICE = 170

EVENTS = {
    "30 Mayo": "417009905",
    "31 Mayo": "1848567714",
    "2 Junio": "1589736692",
    "3 Junio": "961888291",
    "6 Junio": "1852247887",
    "7 Junio": "1341715816",
    "10 Junio": "412370092",
    "11 Junio": "2035589996",
    "14 Junio": "1378879656",
    "15 Junio": "1566404077",
}

BASE_URL = "https://www.ticketmaster.es/event/"

# ==========================
# TELEGRAM
# ==========================

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# ==========================
# SELENIUM SETUP
# ==========================

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=chrome_options)


# ==========================
# MAIN LOOP
# ==========================

while True:
    print("🔎 Buscando entradas...")

    for date, event_id in EVENTS.items():
        url = BASE_URL + event_id
        driver.get(url)

        time.sleep(5)  # esperar a que cargue el mapa

        seats = driver.find_elements(
            By.CSS_SELECTOR,
            'g[data-component="svg__seat"][type]'
        )

        if seats:
            print(f"🔥 ENTRADAS DETECTADAS {date}")

            for seat in seats[:5]:  # limita para no spamear
                try:
                    seat.click()
                    time.sleep(1)

                    price_element = driver.find_element(
                        By.CSS_SELECTOR,
                        '[data-testid="price"]'
                    )
                    price_text = price_element.text
                    price = int("".join(filter(str.isdigit, price_text)))

                    if price <= MAX_PRICE:
                        send_telegram(
                            f"🎟 Entrada encontrada\n"
                            f"📅 {date}\n"
                            f"💶 {price_text}\n"
                            f"{url}"
                        )

                except:
                    pass

        else:
            print(f"❌ Nada en {date}")

    print("⏳ Esperando 30 segundos...\n")
    time.sleep(30)
