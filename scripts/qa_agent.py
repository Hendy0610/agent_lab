import os
import re
import requests
import anthropic
from github_utils import get_repo, post_comment, set_labels, get_pr_diff, ensure_labels_exist, get_pr_info_from_issue
from telegram_utils import send_message


def get_ci_status(pr_head_sha: str, repo_name: str) -> tuple:
    """Returns (status, summary) where status is 'success', 'failure', 'pending', or 'unknown'."""
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN", "")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(
        f"https://api.github.com/repos/{repo_name}/commits/{pr_head_sha}/check-runs",
        headers=headers
    )
    if r.status_code != 200:
        return "unknown", "CI-Status konnte nicht abgerufen werden."
    data = r.json()
    runs = data.get("check_runs", [])
    if not runs:
        return "unknown", "Keine CI-Checks gefunden."
    failed = [r for r in runs if r["conclusion"] in ("failure", "timed_out", "cancelled")]
    pending = [r for r in runs if r["status"] in ("in_progress", "queued", "waiting")]
    passed = [r for r in runs if r["conclusion"] == "success"]
    if failed:
        names = ", ".join(r["name"] for r in failed)
        return "failure", f"❌ Fehlgeschlagene Checks: {names}"
    if pending:
        names = ", ".join(r["name"] for r in pending)
        return "pending", f"⏳ Laufende Checks: {names}"
    return "success", f"✅ Alle {len(passed)} Checks bestanden."

SYSTEM_PROMPT = """Du bist der QA & Architecture Agent für Hendriks repo-gebundenes Multi-Agent-Entwicklungssystem.

Du prüfst jeden Pull Request vor dem Merge.

Dein Ergebnis muss eindeutig sein:
- APPROVED
- CHANGES_REQUESTED
- BLOCKED

Bei CHANGES_REQUESTED oder BLOCKED musst du konkret sagen was das Problem ist, warum es relevant ist, und was geändert werden muss.

Du darfst nicht mergen."""


def main():
    # QA agent is triggered by /ready-for-qa comment on an issue
    issue_repo = get_repo()  # always agent_lab (where the issue lives)
    issue_number = int(os.environ["ISSUE_NUMBER"])
    issue = issue_repo.get_issue(issue_number)

    ensure_labels_exist()

    # Get PR info from issue comments
    target_repo_name, pr_number = get_pr_info_from_issue(issue)

    if not pr_number:
        # Fallback: try PR_NUMBER env var (legacy support)
        pr_number_env = os.environ.get("PR_NUMBER", "")
        if pr_number_env:
            pr_number = int(pr_number_env)
            target_repo_name = "Hendy0610/agent_lab"
        else:
            print("No PR info found, exiting")
            return

    if not target_repo_name:
        target_repo_name = "Hendy0610/agent_lab"

    # Get PR from target repo
    target_repo = get_repo(target_repo_name)
    pr = target_repo.get_pull(pr_number)

    # get linked issue requirements
    issue_requirements = ""
    comments = list(issue.get_comments())
    for c in comments:
        if "Anforderungsanalyse" in (c.body or "") or "Requirements Agent" in (c.body or ""):
            issue_requirements = (c.body or "")[:2000]
            break

    diff = get_pr_diff(pr_number, target_repo_name)

    # Check CI status
    ci_status, ci_summary = get_ci_status(pr.head.sha, target_repo_name)
    if ci_status == "failure":
        comment_body = f"""## 🚫 QA & Architecture Agent — CI fehlgeschlagen

**CI-Status:** {ci_summary}

QA-Review wird nicht durchgeführt, solange CI-Checks fehlschlagen.
Bitte behebe die Fehler und warte auf grüne Checks.

/blocked CI-Checks fehlgeschlagen

*QA & Architecture Agent*"""
        post_comment(pr, comment_body)
        set_labels(pr, ["status/blocked"], ["status/ready-for-qa"])
        send_message(f"🚫 *CI fehlgeschlagen — PR #{pr_number}*\n\n{ci_summary}\n\nQA blockiert bis Checks grün sind.")
        print("QA blocked: CI failing")
        return

    if ci_status == "pending":
        comment_body = f"""## ⏳ QA & Architecture Agent — CI noch nicht abgeschlossen

**CI-Status:** {ci_summary}

QA-Review startet nach Abschluss der CI-Checks.

*QA & Architecture Agent*"""
        post_comment(pr, comment_body)
        print("QA waiting: CI pending")
        return

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    body = pr.body or ""
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

**CI-Status:** {ci_summary}

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
        post_comment(issue, f"/qa-approved\n\nPR #{pr_number} in `{target_repo_name}` wurde vom QA Agent freigegeben.\n\n*QA & Architecture Agent*")
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
