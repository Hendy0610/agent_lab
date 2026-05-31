import os
import re
import time
import requests
from github import Github


def get_github_client():
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN", "")
    return Github(token)


def get_repo(repo_name: str = "Hendy0610/agent_lab"):
    return get_github_client().get_repo(repo_name)


def get_target_repo_name(issue) -> str:
    for comment in issue.get_comments():
        match = re.search(r'<!--\s*TARGET_REPO:\s*([\w\-./]+)\s*-->', comment.body or "")
        if match:
            return match.group(1)
    # also check issue body
    match = re.search(r'<!--\s*TARGET_REPO:\s*([\w\-./]+)\s*-->', issue.body or "")
    if match:
        return match.group(1)
    return "Hendy0610/agent_lab"


def create_repo_if_not_exists(repo_name: str) -> bool:
    """Create repo if it doesn't exist. Returns True if created or already exists."""
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN", "")
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    owner, name = repo_name.split("/", 1)

    # check if exists
    r = requests.get(f"https://api.github.com/repos/{repo_name}", headers=headers)
    if r.status_code == 200:
        return True  # already exists

    # create it
    r = requests.post(
        "https://api.github.com/user/repos",
        headers=headers,
        json={
            "name": name,
            "description": "Project managed by Agent Lab",
            "private": False,
            "auto_init": True  # creates main branch with README
        }
    )
    if r.status_code == 201:
        print(f"Created repo: {repo_name}")
        time.sleep(3)  # wait for GitHub to initialize
        return True
    else:
        print(f"Failed to create repo: {r.text}")
        return False


def get_pr_info_from_issue(issue) -> tuple:
    """Returns (repo_name, pr_number) from issue comments."""
    for comment in issue.get_comments():
        match = re.search(r'<!--\s*PR_INFO:\s*repo=([\w\-./]+)\s+pr=(\d+)\s*-->', comment.body or "")
        if match:
            return match.group(1), int(match.group(2))
    return None, None


def post_comment(issue_or_pr, body: str):
    issue_or_pr.create_comment(body)


def set_labels(issue_or_pr, labels_to_add: list, labels_to_remove: list = None):
    current = [l.name for l in issue_or_pr.labels]
    if labels_to_remove:
        current = [l for l in current if l not in labels_to_remove]
    new_labels = list(set(current + labels_to_add))
    issue_or_pr.set_labels(*new_labels)


def get_pr_diff(pr_number: int, repo_name: str = "Hendy0610/agent_lab") -> str:
    token = os.environ.get("GH_PAT") or os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3.diff"
    }
    r = requests.get(
        f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}",
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
