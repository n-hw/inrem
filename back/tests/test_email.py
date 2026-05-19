"""Tests for the email service — provider selection + Gmail send/fail paths.

We don't open a real SMTP socket; `aiosmtplib.send` is mocked.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services import email_service
from app.services.email_service import (
    GmailSMTPProvider,
    MockEmailProvider,
    _build_default_provider,
)


def _reset_provider():
    email_service._email_provider = None


def test_default_provider_is_mock_when_env_missing(monkeypatch):
    monkeypatch.setattr(email_service.settings, "GMAIL_USERNAME", None)
    monkeypatch.setattr(email_service.settings, "GMAIL_APP_PASSWORD", None)
    provider = _build_default_provider()
    assert isinstance(provider, MockEmailProvider)


def test_default_provider_is_gmail_when_env_set(monkeypatch):
    monkeypatch.setattr(email_service.settings, "GMAIL_USERNAME", "x@gmail.com")
    monkeypatch.setattr(email_service.settings, "GMAIL_APP_PASSWORD", "appp")
    monkeypatch.setattr(email_service.settings, "GMAIL_FROM_NAME", None)
    provider = _build_default_provider()
    assert isinstance(provider, GmailSMTPProvider)
    assert provider.username == "x@gmail.com"
    assert provider.from_name == "InRem"  # default


@pytest.mark.asyncio
async def test_gmail_provider_sends_with_correct_args():
    """`aiosmtplib.send` must be called with the configured host/credentials."""
    provider = GmailSMTPProvider(
        username="alerts@gmail.com",
        app_password="appp",
        from_name="InRem",
    )
    with patch(
        "app.services.email_service.aiosmtplib.send",
        new=AsyncMock(return_value=None),
    ) as send_mock:
        ok = await provider.send_email(
            to_email="user@example.com",
            subject="hello",
            body_text="hi",
            body_html="<p>hi</p>",
        )
    assert ok is True
    send_mock.assert_awaited_once()
    kwargs = send_mock.call_args.kwargs
    assert kwargs["hostname"] == "smtp.gmail.com"
    assert kwargs["port"] == 587
    assert kwargs["username"] == "alerts@gmail.com"
    assert kwargs["password"] == "appp"
    assert kwargs["start_tls"] is True


@pytest.mark.asyncio
async def test_gmail_provider_returns_false_on_smtp_failure(caplog):
    """SMTP errors must be logged at ERROR and surfaced as `False` return."""
    import logging

    provider = GmailSMTPProvider(
        username="alerts@gmail.com",
        app_password="appp",
    )
    caplog.set_level(logging.ERROR)
    with patch(
        "app.services.email_service.aiosmtplib.send",
        new=AsyncMock(side_effect=ConnectionRefusedError("boom")),
    ):
        ok = await provider.send_email(
            to_email="x@example.com",
            subject="s",
            body_text="b",
        )
    assert ok is False
    assert any("gmail_send_failed" in r.getMessage() for r in caplog.records)


@pytest.mark.asyncio
async def test_mock_provider_is_a_noop_returning_true():
    provider = MockEmailProvider()
    ok = await provider.send_email("x@example.com", "s", "b")
    assert ok is True
