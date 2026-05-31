import os
import requests
from github import Github


def get_github_client():
    token = os.environ["GITHUB_TOKEN"]
    return Github(token)


def get_repo():
    return get_github_client().get_repo("Hendy0610/agent_lab")


def post_comment(issue_or_pr, body: str):
    issue_or_pr.create_comment(body)


def set_labels(issue_or_pr, labels_to_add: list, labels_to_remove: list = None):
    current = [l.name for l in issue_or_pr.labels]
    if labels_to_remove:
        current = [l for l in current if l not in labels_to_remove]
    new_labels = list(set(current + labels_to_add))
    issue_or_pr.set_labels(*new_labels)


def get_pr_diff(pr_number: int) -> str:
    token = os.environ["GITHUB_TOKEN"]
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    r = requests.get(
        f"https://api.github.com/repos/Hendy0610/agent_lab/pulls/{pr_number}",
        headers=headers
    )
    return r.text


def read_file_from_repo(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return ""


def ensure_labels_exist():
    """Create all required labels if they don't exist."""
    repo = get_repo()
    required_labels = [
        ("status/idea-received", "0075ca"),
        ("status/requirements-drafted", "e4e669"),
        ("status/waiting-for-requirements-approval", "fbca04"),
        ("status/approved-for-development", "0e8a16"),
        ("status/in-development", "1d76db"),
        ("status/pr-created", "1d76db"),
        ("status/ready-for-qa", "e99695"),
        ("status/qa-in-progress", "f9d0c4"),
        ("status/qa-approved", "0e8a16"),
        ("status/changes-requested", "d93f0b"),
        ("status/blocked", "b60205"),
        ("status/showcase-ready", "c5def5"),
        ("status/waiting-for-merge-approval", "fbca04"),
        ("status/approved-to-merge", "0e8a16"),
        ("status/merged", "6f42c1"),
        ("status/done", "6f42c1"),
        ("agent/requirements", "bfd4f2"),
        ("agent/developer", "bfd4f2"),
        ("agent/qa-architecture", "bfd4f2"),
        ("type/feature", "84b6eb"),
        ("type/bugfix", "ee0701"),
        ("type/chore", "fef2c0"),
        ("type/refactor", "e4e669"),
        ("type/documentation", "0075ca"),
        ("risk/low", "c2e0c6"),
        ("risk/medium", "fef2c0"),
        ("risk/high", "f9d0c4"),
        ("risk/security", "b60205"),
        ("risk/privacy", "b60205"),
        ("risk/architecture", "e99695"),
        ("risk/breaking-change", "b60205"),
    ]
    existing = {l.name for l in repo.get_labels()}
    for name, color in required_labels:
        if name not in existing:
            try:
                repo.create_label(name, color)
            except Exception:
                pass
