import os
import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _token():
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def _chat_id():
    return os.environ.get("TELEGRAM_CHAT_ID", "")


def send_message(text: str, parse_mode: str = "Markdown", buttons: list = None) -> dict:
    """Send a text message, optionally with inline keyboard buttons.

    buttons format: [[("Label", "callback_data"), ...], ...]
    Each inner list is a row of buttons.
    """
    token = _token()
    chat_id = _chat_id()
    if not token or not chat_id:
        print(f"Telegram not configured, skipping: {text[:100]}")
        return {}
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": label, "callback_data": data} for label, data in row]
                for row in buttons
            ]
        }
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json=payload)
    return r.json()


def send_photo(image_path: str, caption: str, buttons: list = None) -> dict:
    """Send a photo, optionally with inline keyboard buttons."""
    token = _token()
    chat_id = _chat_id()
    if not token or not chat_id:
        print("Telegram not configured, skipping photo")
        return {}
    data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
    if buttons:
        import json
        data["reply_markup"] = json.dumps({
            "inline_keyboard": [
                [{"text": label, "callback_data": cb} for label, cb in row]
                for row in buttons
            ]
        })
    with open(image_path, "rb") as f:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data=data,
            files={"photo": f}
        )
    return r.json()


def answer_callback_query(callback_query_id: str, text: str = "") -> dict:
    """Acknowledge a button press (required by Telegram API)."""
    token = _token()
    r = requests.post(
        f"https://api.telegram.org/bot{token}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id, "text": text}
    )
    return r.json()


def get_updates(offset: int = None) -> list:
    token = _token()
    params = {"timeout": 0, "limit": 100}
    if offset is not None:
        params["offset"] = offset
    r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", params=params)
    data = r.json()
    if not data.get("ok"):
        return []
    return data.get("result", [])
