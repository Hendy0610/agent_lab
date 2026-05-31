import os
import re
import subprocess
from pathlib import Path
import anthropic
from github_utils import get_repo, post_comment, set_labels, ensure_labels_exist

SYSTEM_PROMPT = """Du bist der Developer Agent für Hendriks repo-gebundenes Multi-Agent-Entwicklungssystem.

Du implementierst ausschließlich freigegebene Issues in diesem Repository: https://github.com/Hendy0610/agent_lab

Du darfst:
- Dateien lesen, erstellen und bearbeiten
- Code implementieren
- Tests schreiben
- Dokumentation anpassen

Du darfst nicht:
- direkt auf main pushen
- ohne QA-Approval mergen
- den Scope eigenmächtig erweitern

Wenn du fertig bist, rufe task_complete auf."""


def run_git(args: list, cwd: str = ".") -> str:
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"git {' '.join(args)}: {result.stderr}")
    return result.stdout + result.stderr


def get_repo_tree(root: str = ".") -> str:
    lines = []
    for p in sorted(Path(root).rglob("*")):
        if ".git" in p.parts:
            continue
        rel = str(p.relative_to(root))
        lines.append(rel)
    return "\n".join(lines)


def main():
    repo = get_repo()
    issue_number = int(os.environ["ISSUE_NUMBER"])
    issue = repo.get_issue(issue_number)

    ensure_labels_exist()

    # Gather requirements from issue and comments
    comments = list(issue.get_comments())
    requirements_text = f"# {issue.title}\n\n{issue.body or ''}\n\n"
    for c in comments:
        if "Requirements Agent" in (c.body or "") or "Anforderungsanalyse" in (c.body or ""):
            requirements_text += f"\n---\n{c.body}"
            break

    # Create branch name
    slug = re.sub(r'[^a-z0-9]+', '-', issue.title.lower()).strip('-')[:40]
    branch_name = f"feature/{issue_number}-{slug}"

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    tools = [
        {
            "name": "read_file",
            "description": "Read the content of a file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "write_file",
            "description": "Write content to a file (creates directories as needed)",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to repo root"},
                    "content": {"type": "string", "description": "File content"}
                },
                "required": ["path", "content"]
            }
        },
        {
            "name": "list_directory",
            "description": "List files in a directory",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path (default: .)"}
                },
                "required": []
            }
        },
        {
            "name": "task_complete",
            "description": "Call this when implementation is done",
            "input_schema": {
                "type": "object",
                "properties": {
                    "pr_title": {"type": "string", "description": "Pull request title"},
                    "pr_body": {"type": "string", "description": "Pull request description in markdown"}
                },
                "required": ["pr_title", "pr_body"]
            }
        }
    ]

    repo_tree = get_repo_tree(".")

    messages = [
        {
            "role": "user",
            "content": f"""Implementiere das folgende freigegebene Issue.

**Repository-Struktur:**
{repo_tree}

**Anforderungen:**
{requirements_text[:4000]}

Arbeite die Anforderungen durch, erstelle oder modifiziere die nötigen Dateien,
und rufe am Ende task_complete auf mit einem PR-Titel und einer PR-Beschreibung.

Halte dich strikt an die Anforderungen. Keine unnötigen Zusätze."""
        }
    ]

    pr_title = None
    pr_body = None

    # Tool use loop
    for _ in range(20):  # max iterations
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            break

        if response.stop_reason != "tool_use":
            break

        tool_results = []
        done = False

        for block in response.content:
            if block.type != "tool_use":
                continue

            tool_name = block.name
            tool_input = block.input
            result = ""

            if tool_name == "read_file":
                path = tool_input["path"]
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        result = f.read()
                except Exception as e:
                    result = f"Error: {e}"

            elif tool_name == "write_file":
                path = tool_input["path"]
                content = tool_input["content"]
                try:
                    Path(path).parent.mkdir(parents=True, exist_ok=True)
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    result = f"Written: {path}"
                except Exception as e:
                    result = f"Error: {e}"

            elif tool_name == "list_directory":
                path = tool_input.get("path", ".")
                try:
                    entries = sorted(os.listdir(path))
                    result = "\n".join(entries)
                except Exception as e:
                    result = f"Error: {e}"

            elif tool_name == "task_complete":
                pr_title = tool_input["pr_title"]
                pr_body = tool_input["pr_body"]
                result = "Task marked as complete"
                done = True

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result
            })

        messages.append({"role": "user", "content": tool_results})

        if done:
            break

    if not pr_title:
        pr_title = f"[#{issue_number}] {issue.title}"
    if not pr_body:
        pr_body = f"## Summary\n\nImplementation for issue #{issue_number}\n\n## Linked Issue\n\nCloses #{issue_number}"

    # Git operations
    run_git(["checkout", "-b", branch_name])
    run_git(["add", "-A"])
    run_git(["commit", "-m", f"[#{issue_number}] {issue.title}"])
    run_git(["push", "-u", "origin", branch_name])

    # Create PR
    gh_repo = get_repo()
    pr = gh_repo.create_pull(
        title=f"[#{issue_number}] {pr_title}",
        body=pr_body + f"\n\nCloses #{issue_number}",
        head=branch_name,
        base="main"
    )

    set_labels(pr, ["status/ready-for-qa", "agent/qa-architecture"])

    post_comment(issue,
                 f"""/development-started

Implementierung abgeschlossen.

/pr-created {pr.html_url}

/ready-for-qa

*Developer Agent*""")

    set_labels(issue, ["status/pr-created"], ["status/approved-for-development", "status/in-development"])

    print(f"PR created: {pr.html_url}")


if __name__ == "__main__":
    main()
