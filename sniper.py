import requests
import os
import json
import sys

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# IDs de eventos/fechas de Ticketmaster
event_ids = [
    "417009905",   # 30 mayo
    "1848567714",  # 31 mayo
    "1589736692",  # 2 junio
    "961888291",   # 3 junio
    "1852247887",  # 6 junio
    "1341715816",  # 7 junio
    "412370092",   # 10 junio
    "2035589996",  # 11 junio
    "1378879656",  # 14 junio
    "1566404077",  # 15 junio
]

# Precio máximo para notificación en céntimos de euro
MAX_PRICE = 16000  # 160€

# Archivo temporal para anti-spam
STATE_FILE = "sent_alerts.json"

# -----------------------------
# FUNCIONES
# -----------------------------

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_telegram(msg):
    """Envía mensaje a Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ No hay BOT_TOKEN o CHAT_ID configurados")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    try:
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        print(f"Error enviando Telegram: {e}")

def check_event(event_id):
    """Revisa la disponibilidad de un evento"""
    url = f"https://availability.ticketmaster.es/api/v2/TM_ES/availability/{event_id}?subChannelId=1"
    try:
        resp = requests.get(url, timeout=10).json()
    except Exception as e:
        print(f"Error al consultar evento {event_id}: {e}")
        return [], []

    official_entries = []
    resale_entries = []

    for offer in resp.get("offers", []):
        price = offer.get("price", {}).get("total", 0)
        offer_type = offer.get("type", "").lower()
        description = offer.get("offerTypeDescription", "Sin descripción")

        # Clasificamos resale vs oficial
        if offer_type == "resale":
            resale_entries.append({"price": price, "description": description})
        else:
            if price <= MAX_PRICE:
                official_entries.append({"price": price, "description": description})

    return official_entries, resale_entries

# -----------------------------
# LOOP PRINCIPAL
# -----------------------------
state = load_state()

for eid in event_ids:
    official, resale = check_event(eid)

    # Notificación Telegram solo para entradas oficiales
    new_officials = []
    for o in official:
        key = f"{eid}-{o['description']}-{o['price']}"
        if key not in state:
            new_officials.append(o)
            state[key] = True

    if new_officials:
        msg = f"🎯 Entradas oficiales disponibles para evento {eid}:\n"
        for o in new_officials:
            msg += f"- {o['description']} | {o['price']/100:.2f}€\n"
        send_telegram(msg)

    # Resale solo en consola/logs
    if resale:
        print(f"⚠️ Resale detectado para evento {eid}:")
        for r in resale:
            print(f"- {r['description']} | {r['price']/100:.2f}€")
        sys.stdout.flush()  # <-- fuerza que GitHub Actions lo muestre

# Guardamos estado
save_state(state)

