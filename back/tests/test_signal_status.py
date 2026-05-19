"""Tests for the read-only /signal/status endpoint."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        email="user@inrem.test",
        is_active=True,
        last_active_at=datetime.utcnow() - timedelta(minutes=5),
        deletion_requested_at=None,
    )


@pytest.fixture
def override_deps(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    yield
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_status_returns_last_active_at(async_client, override_deps, mock_user):
    resp = await async_client.get(
        "/api/v1/signal/status",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["last_active_at"] is not None
    assert body["deletion_requested_at"] is None


@pytest.mark.asyncio
async def test_status_reflects_pending_deletion(async_client, override_deps, mock_user):
    mock_user.deletion_requested_at = datetime.utcnow() - timedelta(days=2)
    resp = await async_client.get(
        "/api/v1/signal/status",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["deletion_requested_at"] is not None


@pytest.mark.asyncio
async def test_status_does_not_call_record_heartbeat(async_client, override_deps):
    """Polling endpoint must not register a new activity signal."""
    from unittest.mock import patch

    with patch(
        "app.services.signal_service.record_heartbeat",
        new=AsyncMock(),
    ) as svc:
        resp = await async_client.get(
            "/api/v1/signal/status",
            headers={"Authorization": "Bearer test"},
        )
    assert resp.status_code == 200
    svc.assert_not_called()
