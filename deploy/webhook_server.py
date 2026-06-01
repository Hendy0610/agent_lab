"""Telegram Webhook Server for Agent Lab Bot.

Receives Telegram messages instantly via webhook and processes commands.
Triggers GitHub Actions workflows via API for agent tasks.

Run with: uvicorn webhook_server:app --host 0.0.0.0 --port 8443 --ssl-keyfile server.key --ssl-certfile server.crt
"""
import os
import re
import logging
import requests
from fastapi import FastAPI, Request, HTTPException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
GH_PAT = os.environ["GH_PAT"]
GH_REPO = os.environ.get("GH_REPO", "Hendy0610/agent_lab")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
GITHUB_API = "https://api.github.com"
GH_HEADERS = {
    "Authorization": f"token {GH_PAT}",
    "Accept": "application/vnd.github.v3+json",
}


# ---------------------------------------------------------------------------
# Telegram helpers
# ---------------------------------------------------------------------------

MAIN_KEYBOARD = {
    "keyboard": [
        [{"text": "📋 Status"}, {"text": "💡 Neue Idee"}],
        [{"text": "✅ Approve"}, {"text": "🎨 Design freigeben"}],
        [{"text": "🔀 Merge"}, {"text": "🔒 Issue schließen"}],
    ],
    "resize_keyboard": True,
    "persistent": True,
}


def send_message(text: str, buttons: list = None, use_keyboard: bool = False) -> None:
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    if buttons:
        payload["reply_markup"] = {
            "inline_keyboard": [
                [{"text": label, "callback_data": data} for label, data in row]
                for row in buttons
            ]
        }
    elif use_keyboard:
        payload["reply_markup"] = MAIN_KEYBOARD
    r = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=10)
    if not r.ok:
        logger.error("Telegram sendMessage failed: %s", r.text[:200])


def answer_callback(callback_id: str, text: str = "") -> None:
    requests.post(
        f"{TELEGRAM_API}/answerCallbackQuery",
        json={"callback_query_id": callback_id, "text": text},
        timeout=10,
    )


# ---------------------------------------------------------------------------
# GitHub helpers
# ---------------------------------------------------------------------------

def gh_get(path: str) -> dict:
    r = requests.get(f"{GITHUB_API}/{path}", headers=GH_HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()


def gh_post(path: str, body: dict) -> dict:
    r = requests.post(f"{GITHUB_API}/{path}", headers=GH_HEADERS, json=body, timeout=10)
    r.raise_for_status()
    return r.json()


def gh_patch(path: str, body: dict) -> dict:
    r = requests.patch(f"{GITHUB_API}/{path}", headers=GH_HEADERS, json=body, timeout=10)
    r.raise_for_status()
    return r.json()


def trigger_workflow(workflow_file: str, inputs: dict = None) -> bool:
    """Trigger a GitHub Actions workflow_dispatch event."""
    try:
        requests.post(
            f"{GITHUB_API}/repos/{GH_REPO}/actions/workflows/{workflow_file}/dispatches",
            headers=GH_HEADERS,
            json={"ref": "main", "inputs": inputs or {}},
            timeout=10,
        )
        return True
    except Exception as e:
        logger.error("Failed to trigger workflow %s: %s", workflow_file, e)
        return False


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def handle_idea(text: str) -> None:
    lines = text.strip().split("\n")
    title = lines[0][:200]
    body = "\n".join(lines[1:]).strip() if len(lines) > 1 else title

    labels_needed = ["status/idea-received", "agent/requirements", "type/feature"]
    # ensure labels exist
    existing = {lb["name"] for lb in gh_get(f"repos/{GH_REPO}/labels")}
    label_colors = {
        "status/idea-received": "0075ca",
        "agent/requirements": "e4e669",
        "type/feature": "a2eeef",
    }
    for label in labels_needed:
        if label not in existing:
            try:
                gh_post(f"repos/{GH_REPO}/labels", {"name": label, "color": label_colors.get(label, "ededed")})
            except Exception:
                pass

    issue = gh_post(f"repos/{GH_REPO}/issues", {
        "title": title,
        "body": body,
        "labels": labels_needed,
    })
    send_message(
        f"✅ *Issue erstellt!*\n\nIssue #{issue['number']}: {title}\n\n"
        f"Der Requirements Agent analysiert jetzt deine Idee...",
    )


def handle_approve(issue_number: int) -> None:
    try:
        gh_post(f"repos/{GH_REPO}/issues/{issue_number}/comments", {"body": "/approve-development"})
        send_message(f"✅ *Issue #{issue_number} freigegeben!*\nDer Design Agent erstellt jetzt das UI/UX Design.")
    except Exception as e:
        send_message(f"❌ Fehler bei Freigabe von Issue #{issue_number}: {e}")


def handle_approve_design(issue_number: int) -> None:
    try:
        gh_post(f"repos/{GH_REPO}/issues/{issue_number}/comments", {"body": f"/approve-design {issue_number}"})
        send_message(
            f"✅ *Design für Issue #{issue_number} freigegeben!*\n"
            f"Der Developer Agent startet jetzt mit der Implementierung."
        )
    except Exception as e:
        send_message(f"❌ Fehler: {e}")


def handle_merge(issue_number: int) -> None:
    try:
        gh_post(f"repos/{GH_REPO}/issues/{issue_number}/comments", {"body": "/approve-merge"})
        send_message(f"✅ *Merge für Issue #{issue_number} freigegeben!*\nDer Merge läuft...")
    except Exception as e:
        send_message(f"❌ Fehler beim Merge von Issue #{issue_number}: {e}")


def handle_close(issue_number: int) -> None:
    try:
        issue = gh_get(f"repos/{GH_REPO}/issues/{issue_number}")
        if issue["state"] == "closed":
            send_message(f"ℹ️ Issue #{issue_number} ist bereits geschlossen.")
            return
        gh_patch(f"repos/{GH_REPO}/issues/{issue_number}", {"state": "closed"})
        send_message(f"🔒 *Issue #{issue_number} geschlossen!*\n_{issue['title']}_")
    except Exception as e:
        send_message(f"❌ Fehler beim Schließen von Issue #{issue_number}: {e}")


def handle_status() -> None:
    issues = gh_get(f"repos/{GH_REPO}/issues?state=open&per_page=10")
    if not issues:
        send_message("Keine offenen Issues vorhanden.")
        return
    lines = ["*Offene Issues:*\n"]
    for issue in issues:
        labels = [lb["name"] for lb in issue.get("labels", []) if lb["name"].startswith("status/")]
        status = labels[0].replace("status/", "") if labels else "?"
        lines.append(f"• #{issue['number']}: {issue['title'][:50]} — `{status}`")
    send_message("\n".join(lines))


def handle_callback(callback_query: dict) -> None:
    callback_id = callback_query.get("id", "")
    data = callback_query.get("data", "")
    chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))

    if chat_id != TELEGRAM_CHAT_ID:
        return

    match = re.match(r"^(approve_dev|approve_design|merge):(\d+)$", data)
    if not match:
        answer_callback(callback_id, "Unbekannte Aktion")
        return

    action, num = match.group(1), int(match.group(2))
    if action == "approve_dev":
        answer_callback(callback_id, "✅ Freigabe wird übermittelt...")
        handle_approve(num)
    elif action == "approve_design":
        answer_callback(callback_id, "✅ Design-Freigabe wird übermittelt...")
        handle_approve_design(num)
    elif action == "merge":
        answer_callback(callback_id, "✅ Merge-Freigabe wird übermittelt...")
        handle_merge(num)


# pending state: stores what action the user selected and is waiting for a number
_pending: dict = {}


def process_message(message: dict) -> None:
    from_chat = str(message.get("chat", {}).get("id", ""))
    if from_chat != TELEGRAM_CHAT_ID:
        return

    text = message.get("text", "").strip()
    if not text:
        return

    # Handle pending state (user selected a button and we're waiting for a number)
    if from_chat in _pending:
        action = _pending.pop(from_chat)
        if re.match(r"^\d+$", text):
            num = int(text)
            if action == "approve":
                handle_approve(num)
            elif action == "approve_design":
                handle_approve_design(num)
            elif action == "merge":
                handle_merge(num)
            elif action == "close":
                handle_close(num)
            return
        else:
            send_message("❌ Keine gültige Nummer. Bitte nochmal versuchen.", use_keyboard=True)
            return

    # Keyboard button texts
    if text == "📋 Status":
        handle_status()
        return
    elif text == "💡 Neue Idee":
        send_message("Schreib deine Idee als nächste Nachricht:")
        return
    elif text == "✅ Approve":
        _pending[from_chat] = "approve"
        send_message("Welche Issue-Nummer freigeben?")
        return
    elif text == "🎨 Design freigeben":
        _pending[from_chat] = "approve_design"
        send_message("Welche Issue-Nummer für Design-Freigabe?")
        return
    elif text == "🔀 Merge":
        _pending[from_chat] = "merge"
        send_message("Welche Issue-Nummer mergen?")
        return
    elif text == "🔒 Issue schließen":
        _pending[from_chat] = "close"
        send_message("Welche Issue-Nummer schließen?")
        return

    approve_m = re.match(r"^/approve\s+(\d+)$", text, re.IGNORECASE)
    approve_design_m = re.match(r"^/approve-design\s+(\d+)$", text, re.IGNORECASE)
    merge_m = re.match(r"^/merge\s+(\d+)$", text, re.IGNORECASE)
    close_m = re.match(r"^/close\s+(\d+)$", text, re.IGNORECASE)

    if text.lower() in ("/start", "/help"):
        send_message(
            "👋 *Agent Lab Bot*\n\nNutze die Buttons unten oder tippe direkt eine Idee.",
            use_keyboard=True,
        )
    elif approve_design_m:
        handle_approve_design(int(approve_design_m.group(1)))
    elif approve_m:
        handle_approve(int(approve_m.group(1)))
    elif merge_m:
        handle_merge(int(merge_m.group(1)))
    elif close_m:
        handle_close(int(close_m.group(1)))
    elif text.lower() == "/status":
        handle_status()
    elif not text.startswith("/"):
        handle_idea(text)
    else:
        send_message(
            f"Unbekannter Befehl: `{text}`\n\nVerfügbare Befehle:\n"
            f"• Idee als Text senden\n"
            f"• `/approve <nummer>`\n"
            f"• `/approve-design <nummer>`\n"
            f"• `/merge <nummer>`\n"
            f"• `/close <nummer>`\n"
            f"• `/status`",
            use_keyboard=True,
        )


# ---------------------------------------------------------------------------
# Webhook endpoint
# ---------------------------------------------------------------------------

@app.post("/webhook")
async def webhook(request: Request):
    secret = os.environ.get("WEBHOOK_SECRET", "")
    if secret:
        token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if token != secret:
            raise HTTPException(status_code=403, detail="Forbidden")

    update = await request.json()
    logger.info("Update received: %s", str(update)[:200])

    try:
        if "callback_query" in update:
            handle_callback(update["callback_query"])
        elif "message" in update:
            process_message(update["message"])
    except Exception as e:
        logger.error("Error processing update: %s", e)

    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
