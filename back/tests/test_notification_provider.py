"""Tests for NotificationProvider factory and provider behavior."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from app.services.notification_service import (
    NoopNotificationProvider,
    NotificationConfigError,
    _build_default_provider,
)


def test_noop_provider_returned_when_no_credentials():
    """No FIREBASE_CREDENTIALS_PATH + dev env → NoopNotificationProvider."""
    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.FIREBASE_CREDENTIALS_PATH = None
        mock_settings.ENV = "development"
        provider = _build_default_provider()
    assert isinstance(provider, NoopNotificationProvider)


def test_production_without_credentials_raises():
    """No credentials + ENV=production → NotificationConfigError at startup."""
    with patch("app.services.notification_service.settings") as mock_settings:
        mock_settings.FIREBASE_CREDENTIALS_PATH = None
        mock_settings.ENV = "production"
        with pytest.raises(NotificationConfigError):
            _build_default_provider()


@pytest.mark.asyncio
async def test_noop_send_push_returns_false():
    provider = NoopNotificationProvider()
    result = await provider.send_push("token", "title", "body")
    assert result is False


@pytest.mark.asyncio
async def test_noop_send_multicast_returns_zero_success():
    provider = NoopNotificationProvider()
    result = await provider.send_multicast(["t1", "t2"], "title", "body")
    assert result["success_count"] == 0
    assert result["failure_count"] == 2
    assert set(result["failed_tokens"]) == {"t1", "t2"}
