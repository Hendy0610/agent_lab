import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

def send_message(text: str, parse_mode: str = "Markdown") -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print(f"Telegram not configured, skipping: {text[:100]}")
        return {}
    r = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    )
    return r.json()

def get_updates(offset: int = None) -> list:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    params = {"timeout": 0, "limit": 100}
    if offset is not None:
        params["offset"] = offset
    r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params=params)
    data = r.json()
    if not data.get("ok"):
        return []
    return data.get("result", [])
