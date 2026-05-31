import os
import re
import anthropic
from github_utils import get_repo, post_comment, set_labels, get_pr_diff, ensure_labels_exist
from telegram_utils import send_message

SYSTEM_PROMPT = """Du bist der QA & Architecture Agent für Hendriks repo-gebundenes Multi-Agent-Entwicklungssystem.

Du prüfst jeden Pull Request vor dem Merge.

Dein Ergebnis muss eindeutig sein:
- APPROVED
- CHANGES_REQUESTED
- BLOCKED

Bei CHANGES_REQUESTED oder BLOCKED musst du konkret sagen was das Problem ist, warum es relevant ist, und was geändert werden muss.

Du darfst nicht mergen."""


def main():
    repo = get_repo()
    pr_number = int(os.environ["PR_NUMBER"])
    pr = repo.get_pull(pr_number)

    ensure_labels_exist()

    # get linked issue
    issue = None
    issue_requirements = ""
    body = pr.body or ""
    match = re.search(r'[Cc]loses?\s+#(\d+)', body)
    if match:
        issue_num = int(match.group(1))
        try:
            issue = repo.get_issue(issue_num)
            comments = list(issue.get_comments())
            for c in comments:
                if "Anforderungsanalyse" in (c.body or "") or "Requirements Agent" in (c.body or ""):
                    issue_requirements = c.body[:2000]
                    break
        except Exception:
            pass

    diff = get_pr_diff(pr_number)

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = f"""Führe ein QA-Review für diesen Pull Request durch.

**PR #{pr_number}:** {pr.title}

**PR Beschreibung:**
{body[:1000]}

**Anforderungen (aus Issue):**
{issue_requirements or "(keine Anforderungen gefunden)"}

**Diff:**
```diff
{diff[:6000]}
```

Prüfe:
1. Erfüllt der PR die Akzeptanzkriterien?
2. Sind Tests vorhanden und sinnvoll?
3. Bleibt die Architektur sauber?
4. Ist der Code lesbar und wartbar?
5. Gibt es Security-, Compliance- oder Datenschutzrisiken?
6. Gibt es Breaking Changes?
7. Gibt es unnötige Komplexität?

Gib am Ende deines Reviews eine klare Entscheidung:
**VERDICT: APPROVED** oder **VERDICT: CHANGES_REQUESTED** oder **VERDICT: BLOCKED**

Schreibe auf Deutsch."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}]
    )

    review_text = message.content[0].text

    # Parse verdict
    verdict = "CHANGES_REQUESTED"
    if "VERDICT: APPROVED" in review_text:
        verdict = "APPROVED"
    elif "VERDICT: BLOCKED" in review_text:
        verdict = "BLOCKED"

    verdict_emoji = {"APPROVED": "✅", "CHANGES_REQUESTED": "🔄", "BLOCKED": "🚫"}[verdict]

    comment_body = f"""## {verdict_emoji} QA & Architecture Agent — Review

{review_text}

---
/{verdict.lower().replace('_', '-')}

*QA & Architecture Agent*"""

    post_comment(pr, comment_body)

    if verdict == "APPROVED":
        set_labels(pr, ["status/qa-approved"], ["status/ready-for-qa", "status/qa-in-progress"])
        send_message(f"🔍 *QA abgeschlossen — PR #{pr_number}*\nStatus: ✅ APPROVED\n\nRequirements Agent erstellt jetzt den Showcase...")
        # Also comment on linked issue to trigger showcase
        if issue:
            post_comment(issue, f"/qa-approved\n\nPR #{pr_number} wurde vom QA Agent freigegeben.\n\n*QA & Architecture Agent*")
    elif verdict == "CHANGES_REQUESTED":
        set_labels(pr, ["status/changes-requested"], ["status/ready-for-qa", "status/qa-in-progress"])
        short_review = review_text[:300] + "..."
        send_message(f"🔄 *QA: Änderungen erforderlich — PR #{pr_number}*\n\n{short_review}")
    elif verdict == "BLOCKED":
        set_labels(pr, ["status/blocked"], ["status/ready-for-qa", "status/qa-in-progress"])
        short_review = review_text[:300] + "..."
        send_message(f"🚫 *QA: Geblockt — PR #{pr_number}*\n\n{short_review}")

    print(f"QA review posted: {verdict}")


if __name__ == "__main__":
    main()
