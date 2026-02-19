import requests
import os
import json
import hashlib
from datetime import datetime

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

events = {
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

MAX_PRICE = 17000  # 170€
STATE_FILE = "sent_alerts.json"
RESALE_FILE = "resale_history.json"

# -----------------------------
# ESTADO (ANTI-SPAM)
# -----------------------------

def load_state(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_state(state, file):
    with open(file, "w") as f:
        json.dump(state, f, indent=2)

def generate_hash(event_name, offers):
    raw = event_name + str(offers)
    return hashlib.md5(raw.encode()).hexdigest()

# -----------------------------
# TELEGRAM
# -----------------------------

def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("Error enviando Telegram:", e)

# -----------------------------
# CONSULTA
# -----------------------------

def check_event(event_name, event_id):
    url = f"https://availability.ticketmaster.es/api/v2/TM_ES/availability/{event_id}?subChannelId=1"
    
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"Error consultando {event_name}: {e}")
        return [], []

    official = []
    resale = []

    for offer in data.get("offers", []):
        price = offer.get("price", {}).get("total", 0)
        offer_type = offer.get("type", "").lower()
        description = offer.get("offerTypeDescription", "Entrada")

        if offer_type == "resale":
            resale.append({"description": description, "price": price})
        else:
            if price <= MAX_PRICE:
                official.append({"description": description, "price": price})

    return official, resale

# -----------------------------
# EJECUCIÓN
# -----------------------------

state = load_state(STATE_FILE)
resale_history = load_state(RESALE_FILE)
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for event_name, event_id in events.items():
    official, resale = check_event(event_name, event_id)

    # 👀 RESALE → histórico
    if resale:
        if event_name not in resale_history:
            resale_history[event_name] = []

        for r in resale:
            # Check si ya está en histórico
            exists = any(x["description"] == r["description"] and x["price"] == r["price"] for x in resale_history[event_name])
            if not exists:
                resale_history[event_name].append({
                    "description": r["description"],
                    "price": r["price"],
                    "first_seen": now
                })

        print(f"\n⚠️ Resale detectado para {event_name}:")
        for r in resale:
            print(f"- {r['description']} | {r['price']/100:.2f}€")

    # 🔔 Oficiales con anti-spam
    if official:
        alert_hash = generate_hash(event_name, official)
        if state.get(event_name) == alert_hash:
            print(f"Ya notificado antes para {event_name}, no se repite.")
            continue

        message = (
            f"🎯 *ENTRADAS OFICIALES DISPONIBLES*\n\n"
            f"📅 *{event_name}*\n\n"
        )

        for o in official:
            message += f"🎫 {o['description']}\n💶 {o['price']/100:.2f}€\n\n"

        message += f"🔗 https://www.ticketmaster.es/event/{event_id}"
        send_telegram(message)

        state[event_name] = alert_hash

# Guardamos estado actualizado
save_state(state, STATE_FILE)
save_state(resale_history, RESALE_FILE)
