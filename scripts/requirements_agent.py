import os
import anthropic
from github_utils import get_repo, post_comment, set_labels, ensure_labels_exist
from telegram_utils import send_message

SYSTEM_PROMPT = """Du bist der Requirements Agent für Hendriks repo-gebundenes Multi-Agent-Entwicklungssystem.

Du bist der einzige Eingangspunkt für neue Ideen. Deine Aufgabe ist es, aus groben Ideen klare, umsetzbare Anforderungen zu machen.

Arbeite ausschließlich für dieses Repository: https://github.com/Hendy0610/agent_lab

Erfinde keine externen Produktbereiche und erweitere den Scope nicht ohne Freigabe.

Sprache: Deutsch"""


def process_new_issue():
    repo = get_repo()
    issue_number = int(os.environ["ISSUE_NUMBER"])
    issue = repo.get_issue(issue_number)

    ensure_labels_exist()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Eine neue Idee wurde als GitHub Issue eingereicht. Erstelle daraus strukturierte Anforderungen.

**Issue Titel:** {issue.title}

**Issue Inhalt:**
{issue.body or "(kein Inhalt)"}

Erstelle eine strukturierte Anforderungsanalyse mit folgenden Abschnitten:

## Problemstatement
## Zielbild
## User Story
Als ... möchte ich ..., damit ...
## Akzeptanzkriterien
- [ ] Kriterium 1
## Nicht-Ziele
## Offene Fragen
## Risiken
## Erwarteter Aufwand (klein/mittel/groß)
## Technische Grobeinschätzung

Schreibe alles auf Deutsch. Sei konkret und umsetzbar."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    requirements_text = message.content[0].text

    comment_body = f"""## 📋 Requirements Agent — Anforderungsanalyse

{requirements_text}

---

**Bitte um Freigabe:**
- `/approve-development` — Freigabe für Entwicklung
- `/request-requirements-changes <Beschreibung>` — Änderungswunsch

*Requirements Agent*"""

    post_comment(issue, comment_body)
    send_message(
        f"📋 *Anforderungen bereit — Issue #{issue_number}*\n\n"
        f"*{issue.title}*\n\n"
        f"Der Requirements Agent hat die Anforderungen analysiert.\n\n"
        f"Freigeben mit: `/approve {issue_number}`"
    )
    set_labels(issue,
               ["status/waiting-for-requirements-approval", "agent/requirements"],
               ["status/idea-received"])

    print(f"Requirements posted for issue #{issue_number}")


def process_showcase_request():
    repo = get_repo()
    issue_number = int(os.environ["ISSUE_NUMBER"])
    pr_number = int(os.environ["PR_NUMBER"])
    issue = repo.get_issue(issue_number)
    pr = repo.get_pull(pr_number)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # gather issue comments for requirements context
    comments = [c.body for c in issue.get_comments()]
    requirements_context = "\n\n".join(comments[:3])  # first few comments have requirements

    prompt = f"""Erstelle eine Freigabeanfrage (Showcase) für Hendrik.

**Issue:** #{issue_number} - {issue.title}

**Anforderungskontext:**
{requirements_context[:2000]}

**PR:** #{pr_number} - {pr.title}

**PR Beschreibung:**
{pr.body or "(keine Beschreibung)"}

Erstelle einen Showcase-Bericht nach diesem Format:

# Freigabeanfrage: {pr.title}

## Kurzfassung
## Ausgangsidee
## Umgesetzte Änderungen
## Showcase (wie kann Hendrik die Änderung testen?)
## Akzeptanzkriterien (Tabelle mit Status)
## QA- und Architekturprüfung
- QA-Status: APPROVED
## Relevante Links
- Issue: #{issue_number}
- Pull Request: #{pr_number}

Schreibe auf Deutsch."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    showcase_text = message.content[0].text

    comment_body = f"""{showcase_text}

---

## Entscheidung benötigt

Bitte entscheide mit einem der folgenden Kommentare:

1. `/approve-merge` — Freigegeben zum Merge
2. `/request-release-changes <Beschreibung>` — Änderungen erforderlich
3. `/do-not-merge <Grund>` — Nicht mergen

*Requirements Agent*"""

    post_comment(pr, comment_body)
    # Extract first 500 chars of showcase for the notification
    short_showcase = showcase_text[:500] + "..." if len(showcase_text) > 500 else showcase_text
    send_message(
        f"✅ *QA freigegeben — Issue #{issue_number}*\n\n"
        f"{short_showcase}\n\n"
        f"Merge freigeben mit: `/merge {issue_number}`"
    )
    set_labels(pr,
               ["status/waiting-for-merge-approval"],
               ["status/qa-approved"])

    print(f"Showcase posted for PR #{pr_number}")


if __name__ == "__main__":
    trigger = os.environ.get("TRIGGER", "new_issue")
    if trigger == "new_issue":
        process_new_issue()
    elif trigger == "showcase_request":
        process_showcase_request()
