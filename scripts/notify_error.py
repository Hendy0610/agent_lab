"""Send a Telegram error notification for a failed GitHub Actions workflow.

All context is read from environment variables so this script can be called
from any workflow step with `if: failure()`.

Required env vars (Telegram):
    TELEGRAM_BOT_TOKEN  — bot token from @BotFather
    TELEGRAM_CHAT_ID    — recipient chat ID

Context env vars (set automatically by GitHub Actions):
    GITHUB_WORKFLOW     — workflow name
    GITHUB_REPOSITORY   — owner/repo
    GITHUB_REF_NAME     — branch name
    GITHUB_SHA          — commit SHA
    GITHUB_RUN_ID       — Actions run ID
    GITHUB_SERVER_URL   — e.g. https://github.com
    FAILED_JOB          — optional: name of the failed job/step (caller-supplied)
    ERROR_CONTEXT       — optional: short error description (caller-supplied)
"""
import os
import sys
import requests


def build_message() -> str:
    workflow = os.environ.get("GITHUB_WORKFLOW", "unknown workflow")
    repo = os.environ.get("GITHUB_REPOSITORY", "unknown/repo")
    branch = os.environ.get("GITHUB_REF_NAME", "unknown-branch")
    sha = os.environ.get("GITHUB_SHA", "")[:7]
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    failed_job = os.environ.get("FAILED_JOB", "")
    error_context = os.environ.get("ERROR_CONTEXT", "")

    run_url = f"{server_url}/{repo}/actions/runs/{run_id}" if run_id else ""

    lines = [
        "🚨 *Workflow fehlgeschlagen*",
        "",
        f"*Workflow:* `{workflow}`",
        f"*Repository:* `{repo}`",
        f"*Branch:* `{branch}`",
        f"*Commit:* `{sha}`",
    ]
    if failed_job:
        lines.append(f"*Job/Schritt:* `{failed_job}`")
    if error_context:
        lines.append(f"*Fehler:* {error_context}")
    if run_url:
        lines.append(f"*Run:* [Zum Workflow-Run]({run_url})")

    return "\n".join(lines)


def send_notification(dry_run: bool = False) -> bool:
    """Send the error notification. Returns True on success."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("ERROR: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set — cannot send notification.")
        print("Set both secrets in the repository settings.")
        return False

    message = build_message()

    if dry_run:
        print("DRY RUN — message that would be sent:")
        print(message)
        return True

    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
        if r.status_code == 200:
            print("Error notification sent via Telegram.")
            return True
        else:
            print(f"Telegram API error {r.status_code}: {r.text[:200]}")
            return False
    except requests.RequestException as exc:
        print(f"Network error sending Telegram notification: {exc}")
        return False


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    success = send_notification(dry_run=dry_run)
    sys.exit(0 if success else 1)
