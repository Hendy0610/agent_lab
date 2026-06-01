"""Tests for QA Agent memory awareness (get_memory_content)."""
import sys
import os
import base64
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

os.environ.setdefault("GITHUB_TOKEN", "test-token")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "")
os.environ.setdefault("TELEGRAM_CHAT_ID", "")


from qa_agent import get_memory_content


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data


def _encoded(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


def test_memory_ok():
    """MEMORY.md exists and is returned correctly."""
    content = "# MEMORY\nGovernance rule: no direct pushes to main."
    mock_resp = FakeResponse(200, {"content": _encoded(content)})
    with patch("qa_agent.requests.get", return_value=mock_resp):
        text, status = get_memory_content("owner/repo")
    assert status == "ok"
    assert "Governance rule" in text


def test_memory_missing():
    """MEMORY.md does not exist — returns missing status."""
    with patch("qa_agent.requests.get", return_value=FakeResponse(404)):
        text, status = get_memory_content("owner/repo")
    assert status == "missing"
    assert text == ""


def test_memory_api_error():
    """GitHub API returns unexpected error — returns error status."""
    with patch("qa_agent.requests.get", return_value=FakeResponse(500)):
        text, status = get_memory_content("owner/repo")
    assert status == "error"
    assert text == ""


def test_memory_content_truncation_safe():
    """Large MEMORY.md is read without crashing (truncation happens in prompt assembly)."""
    big_content = "x" * 10_000
    mock_resp = FakeResponse(200, {"content": _encoded(big_content)})
    with patch("qa_agent.requests.get", return_value=mock_resp):
        text, status = get_memory_content("owner/repo")
    assert status == "ok"
    assert len(text) == 10_000
