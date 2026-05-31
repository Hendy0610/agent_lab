import os
import sys
import re
import requests
from telegram_utils import send_message, get_updates
from github_utils import get_repo, ensure_labels_exist

def handle_idea(text: str, repo):
    """Create a GitHub issue from the idea text."""
    ensure_labels_exist()
    # Use first line as title, rest as body
    lines = text.strip().split('\n')
    title = lines[0][:200]
    body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""

    issue = repo.create_issue(
        title=title,
        body=body or title,
        labels=["status/idea-received", "agent/requirements", "type/feature"]
    )
    send_message(f"✅ *Issue erstellt!*\n\nIssue #{issue.number}: {title}\n\nDer Requirements Agent analysiert jetzt deine Idee...")
    return issue

def handle_approve(issue_number: int, repo):
    """Post approve-development comment on issue (triggers Design Agent)."""
    try:
        issue = repo.get_issue(issue_number)
        issue.create_comment("/approve-development")
        send_message(f"✅ *Issue #{issue_number} freigegeben!*\nDer Design Agent erstellt jetzt das UI/UX Design.")
    except Exception as e:
        send_message(f"❌ Fehler bei Freigabe von Issue #{issue_number}: {e}")

def handle_approve_design(issue_number: int, repo):
    """Post approve-design comment on issue (triggers Developer Agent)."""
    try:
        issue = repo.get_issue(issue_number)
        issue.create_comment(f"/approve-design {issue_number}")
        send_message(f"✅ *Design für Issue #{issue_number} freigegeben!*\nDer Developer Agent startet jetzt mit der Implementierung.")
    except Exception as e:
        send_message(f"❌ Fehler: {e}")

def handle_merge(issue_number: int, repo):
    """Post approve-merge comment on issue."""
    try:
        issue = repo.get_issue(issue_number)
        issue.create_comment("/approve-merge")
        send_message(f"✅ *Merge für Issue #{issue_number} freigegeben!*\nDer Merge läuft...")
    except Exception as e:
        send_message(f"❌ Fehler beim Merge von Issue #{issue_number}: {e}")

def handle_status(repo):
    """List open issues with their status."""
    issues = list(repo.get_issues(state="open"))[:10]
    if not issues:
        send_message("Keine offenen Issues vorhanden.")
        return
    lines = ["*Offene Issues:*\n"]
    for issue in issues:
        labels = [l.name for l in issue.labels if l.name.startswith("status/")]
        status = labels[0].replace("status/", "") if labels else "?"
        lines.append(f"• #{issue.number}: {issue.title[:50]} — `{status}`")
    send_message('\n'.join(lines))

def main():
    last_update_id = int(os.environ.get("LAST_UPDATE_ID", "0"))
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    repo = get_repo()
    updates = get_updates(offset=last_update_id + 1 if last_update_id else None)

    new_max_id = last_update_id

    for update in updates:
        update_id = update.get("update_id", 0)
        new_max_id = max(new_max_id, update_id)

        message = update.get("message", {})
        if not message:
            continue

        # only process messages from the configured chat
        from_chat = str(message.get("chat", {}).get("id", ""))
        if chat_id and from_chat != chat_id:
            continue

        text = message.get("text", "").strip()
        if not text:
            continue

        # Parse commands
        approve_match = re.match(r'^/approve\s+(\d+)$', text, re.IGNORECASE)
        approve_design_match = re.match(r'^/approve-design\s+(\d+)$', text, re.IGNORECASE)
        merge_match = re.match(r'^/merge\s+(\d+)$', text, re.IGNORECASE)

        if approve_design_match:
            handle_approve_design(int(approve_design_match.group(1)), repo)
        elif approve_match:
            handle_approve(int(approve_match.group(1)), repo)
        elif merge_match:
            handle_merge(int(merge_match.group(1)), repo)
        elif text.lower() == '/status':
            handle_status(repo)
        elif not text.startswith('/'):
            handle_idea(text, repo)
        else:
            send_message(f"Unbekannter Befehl: `{text}`\n\nVerfügbare Befehle:\n• Idee als Text senden\n• `/approve <nummer>`\n• `/approve-design <nummer>`\n• `/merge <nummer>`\n• `/status`")

    # Output new offset for the workflow to save
    print(f"NEW_OFFSET={new_max_id}")

if __name__ == "__main__":
    main()
