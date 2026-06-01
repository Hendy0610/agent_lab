"""Tests for notify_error.py — Telegram error notification script."""
import os
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import notify_error


def _set_github_env(**kwargs):
    defaults = {
        "GITHUB_WORKFLOW": "CI Quality Gate",
        "GITHUB_REPOSITORY": "Hendy0610/agent_lab",
        "GITHUB_REF_NAME": "feature/test",
        "GITHUB_SHA": "abc1234def5678",
        "GITHUB_RUN_ID": "9876543210",
        "GITHUB_SERVER_URL": "https://github.com",
        "FAILED_JOB": "",
        "ERROR_CONTEXT": "",
        "TELEGRAM_BOT_TOKEN": "fake-token",
        "TELEGRAM_CHAT_ID": "123456",
    }
    defaults.update(kwargs)
    return patch.dict(os.environ, defaults, clear=False)


def test_build_message_contains_required_fields():
    with _set_github_env(FAILED_JOB="Syntax & Lint", ERROR_CONTEXT="flake8 error"):
        msg = notify_error.build_message()
    assert "CI Quality Gate" in msg
    assert "Hendy0610/agent_lab" in msg
    assert "feature/test" in msg
    assert "abc1234" in msg  # SHA truncated to 7
    assert "Syntax & Lint" in msg
    assert "flake8 error" in msg
    assert "9876543210" in msg  # run ID in URL


def test_build_message_omits_optional_fields_when_empty():
    with _set_github_env(FAILED_JOB="", ERROR_CONTEXT=""):
        msg = notify_error.build_message()
    assert "Job/Schritt" not in msg
    assert "Fehler:" not in msg


def test_dry_run_does_not_call_api():
    with _set_github_env():
        with patch("notify_error.requests.post") as mock_post:
            result = notify_error.send_notification(dry_run=True)
    mock_post.assert_not_called()
    assert result is True


def test_missing_secrets_returns_false():
    env = {"TELEGRAM_BOT_TOKEN": "", "TELEGRAM_CHAT_ID": ""}
    with patch.dict(os.environ, env):
        result = notify_error.send_notification(dry_run=False)
    assert result is False


def test_successful_send():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    with _set_github_env():
        with patch("notify_error.requests.post", return_value=mock_resp) as mock_post:
            result = notify_error.send_notification(dry_run=False)
    assert result is True
    mock_post.assert_called_once()
    # Token is in the API URL (required) but must not appear in the message body
    call_kwargs = mock_post.call_args
    payload = call_kwargs[1].get("json", {})
    assert "fake-token" not in payload.get("text", "")


def test_api_error_returns_false():
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Bad Request"
    with _set_github_env():
        with patch("notify_error.requests.post", return_value=mock_resp):
            result = notify_error.send_notification(dry_run=False)
    assert result is False


def test_network_error_returns_false():
    import requests as req_lib
    with _set_github_env():
        with patch("notify_error.requests.post", side_effect=req_lib.RequestException("timeout")):
            result = notify_error.send_notification(dry_run=False)
    assert result is False
