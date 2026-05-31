import os
import re
import base64
import anthropic
import requests
from pathlib import Path
from github_utils import get_repo, post_comment, set_labels, ensure_labels_exist, get_target_repo_name
from telegram_utils import send_message

SYSTEM_PROMPT = """Du bist der Design Agent für Hendriks repo-gebundenes Multi-Agent-Entwicklungssystem.

Du erstellst UI/UX Designs für freigegebene Anforderungen.

Du erstellst:
- Ein Design-Dokument mit Komponentenstruktur, Farben, Typografie und User Flow
- Einen vollständigen HTML/CSS Mockup (self-contained, kein externes CSS/JS)

Der Mockup soll modern, clean und professionell aussehen.
Nutze ein ansprechendes Farbschema. Verwende nur inline CSS und keine externen Ressourcen.

Sprache für Beschreibungen: Deutsch"""

def screenshot_html(html_content: str, output_path: str) -> bool:
    """Screenshot HTML using playwright."""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.set_content(html_content)
            page.wait_for_timeout(500)
            page.screenshot(path=output_path, full_page=True)
            browser.close()
        return True
    except Exception as e:
        print(f"Screenshot failed: {e}")
        return False

def send_telegram_photo(image_path: str, caption: str):
    """Send photo via Telegram Bot API."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("Telegram not configured")
        return
    with open(image_path, "rb") as f:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendPhoto",
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
            files={"photo": f}
        )

def upload_image_to_github(image_path: str, repo_name: str = "Hendy0610/agent_lab") -> str:
    """Upload image to GitHub and return markdown image reference."""
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN", "")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

    # Determine branch: use main for non-agent_lab repos
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    if branch != "main" and repo_name != "Hendy0610/agent_lab":
        branch = "main"

    # Upload to repo as a file in .github/designs/
    with open(image_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    filename = Path(image_path).name
    api_url = f"https://api.github.com/repos/{repo_name}/contents/.github/designs/{filename}"

    r = requests.put(api_url, headers=headers, json={
        "message": f"Add design screenshot {filename}",
        "content": content,
        "branch": branch
    })

    if r.status_code in (200, 201):
        raw_url = f"https://raw.githubusercontent.com/{repo_name}/{branch}/.github/designs/{filename}"
        return raw_url
    else:
        print(f"Image upload failed: {r.text}")
        return ""

def main():
    repo = get_repo()
    issue_number = int(os.environ["ISSUE_NUMBER"])
    issue = repo.get_issue(issue_number)

    ensure_labels_exist()

    # Determine target repo
    target_repo = get_target_repo_name(issue)

    # Gather requirements from issue and comments
    requirements_text = f"# {issue.title}\n\n{issue.body or ''}\n\n"
    for comment in issue.get_comments():
        body = comment.body or ""
        if "Anforderungsanalyse" in body or "Requirements Agent" in body:
            requirements_text += f"\n---\n{body}"
            break

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Step 1: Generate design document
    design_prompt = f"""Analysiere diese Anforderungen und erstelle ein UI/UX Design.

**Anforderungen:**
{requirements_text[:3000]}

Erstelle:

## 1. Design-Dokument

### Zielbild
### Komponenten
### Farbschema (Hex-Codes angeben)
### Typografie
### User Flow (Schritt für Schritt)
### UX-Hinweise

## 2. HTML/CSS Mockup

Erstelle danach einen vollständigen, self-contained HTML Mockup.
- Kein externes CSS, kein externes JavaScript
- Nur inline Styles oder <style> Tag
- Modern, clean, professionell
- Mobile-first
- Zeige den wichtigsten Screen / die wichtigste Ansicht

Trenne Design-Dokument und HTML klar mit dem Marker: `---HTML_MOCKUP---`"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": design_prompt}]
    )

    response_text = message.content[0].text

    # Split design doc and HTML
    if "---HTML_MOCKUP---" in response_text:
        parts = response_text.split("---HTML_MOCKUP---", 1)
        design_doc = parts[0].strip()
        html_content = parts[1].strip()
        # Extract just the HTML if wrapped in code block
        html_match = re.search(r'```html\s*(.*?)\s*```', html_content, re.DOTALL)
        if html_match:
            html_content = html_match.group(1)
    else:
        design_doc = response_text
        html_content = "<html><body><h1>Mockup konnte nicht generiert werden</h1></body></html>"

    # Screenshot the HTML
    screenshot_path = f"/tmp/design_{issue_number}.png"
    screenshot_ok = screenshot_html(html_content, screenshot_path)

    # Post design document as issue comment
    image_ref = ""
    if screenshot_ok:
        image_url = upload_image_to_github(screenshot_path, target_repo)
        if image_url:
            image_ref = f"\n\n## Mockup\n\n![Design Mockup]({image_url})\n"

    comment_body = f"""## 🎨 Design Agent — UI/UX Design

{design_doc}
{image_ref}

---

Design freigeben mit `/approve-design {issue_number}` oder Änderungswunsch mit `/request-design-changes <Beschreibung>`.

*Design Agent*"""

    post_comment(issue, comment_body)
    set_labels(issue, ["status/design-ready"], ["status/approved-for-development"])

    # Send Telegram notification
    if screenshot_ok and Path(screenshot_path).exists():
        send_telegram_photo(
            screenshot_path,
            f"🎨 *Design bereit — Issue #{issue_number}: {issue.title[:50]}*\n\n"
            f"Freigeben mit: `/approve-design {issue_number}`"
        )
    else:
        send_message(
            f"🎨 *Design bereit — Issue #{issue_number}: {issue.title[:50]}*\n\n"
            f"Design-Dokument wurde im Issue gepostet.\n\n"
            f"Freigeben mit: `/approve-design {issue_number}`"
        )

    print(f"Design posted for issue #{issue_number}")

if __name__ == "__main__":
    main()
