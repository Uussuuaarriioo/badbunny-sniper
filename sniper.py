import requests
import os
import json
import sys

# -----------------------------
# CONFIGURACIÓN
# -----------------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
STATE_FILE = "sent_alerts.json"

# IDs de eventos/fechas de Ticketmaster
event_ids = [
    "417009905",  # 30 mayo
    "1848567714",  # 31 mayo
    "1589736692",  # 2 junio
    "961888291",  # 3 junio
    "1852247887",  # 6 junio
    "1341715816",  # 7 junio
    "412370092",  # 10 junio
    "2035589996",  # 11 junio
    "1378879656",  # 14 junio
    "1566404077",  # 15 junio
]

MAX_PRICE = 17000  # 170€ en céntimos

# -----------------------------
# UTILIDADES
# -----------------------------
def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"official": [], "resale": []}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def send_telegram(msg, silent=False):
    """Envía mensaje a Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ No hay BOT_TOKEN o CHAT_ID configurados")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "disable_notification": silent}
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

        if offer_type == "resale":
            resale_entries.append({"price": price, "description": description, "id": offer.get("id")})
        else:
            if price <= MAX_PRICE:
                official_entries.append({"price": price, "description": description, "id": offer.get("id")})

    return official_entries, resale_entries

# -----------------------------
# LOOP PRINCIPAL
# -----------------------------
state = load_state()

for eid in event_ids:
    official, resale = check_event(eid)

    # Oficial
    new_official = [o for o in official if o["id"] not in state["official"]]
    if new_official:
        msg = f"🎯 Entradas oficiales disponibles para evento {eid}:\n"
        for o in new_official:
            msg += f"- {o['description']} | {o['price']/100:.2f}€\n"
            state["official"].append(o["id"])
        send_telegram(msg, silent=False)

    # Resale
    new_resale = [r for r in resale if r["id"] not in state["resale"]]
    if new_resale:
        msg = f"⚠️ Resale detectado para evento {eid}:\n"
        for r in new_resale:
            msg += f"- {r['description']} | {r['price']/100:.2f}€\n"
            state["resale"].append(r["id"])
        # Mensaje a Telegram pero sin notificación
        send_telegram(msg, silent=True)

    # Consola para ver todo en GitHub Actions
    if new_official or new_resale:
        print(msg)
        sys.stdout.flush()

save_state(state)

