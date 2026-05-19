"""Tests for account deletion / restore (PIPA 잊혀질 권리)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.services import account_service


@pytest.fixture
def mock_user():
    return User(
        id=uuid4(),
        email="user@inrem.test",
        is_active=True,
        deletion_requested_at=None,
    )


@pytest.fixture
def override_deps(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    yield
    app.dependency_overrides = {}


# --- service-level ---


@pytest.mark.asyncio
async def test_request_deletion_sets_timestamp(mock_user):
    db = AsyncMock()
    before = datetime.utcnow()
    user = await account_service.request_deletion(db, user=mock_user)
    assert user.deletion_requested_at is not None
    assert user.deletion_requested_at >= before
    # is_active stays True so the existing session can call restore.
    assert user.is_active is True


@pytest.mark.asyncio
async def test_request_deletion_is_idempotent(mock_user):
    db = AsyncMock()
    user = await account_service.request_deletion(db, user=mock_user)
    first_stamp = user.deletion_requested_at
    user = await account_service.request_deletion(db, user=mock_user)
    assert user.deletion_requested_at == first_stamp


@pytest.mark.asyncio
async def test_restore_within_grace_clears_stamp(mock_user):
    db = AsyncMock()
    mock_user.deletion_requested_at = datetime.utcnow() - timedelta(days=3)
    user = await account_service.restore(db, user=mock_user)
    assert user.deletion_requested_at is None


@pytest.mark.asyncio
async def test_restore_after_grace_raises_410(mock_user):
    from fastapi import HTTPException

    db = AsyncMock()
    mock_user.deletion_requested_at = datetime.utcnow() - timedelta(days=31)
    with pytest.raises(HTTPException) as exc:
        await account_service.restore(db, user=mock_user)
    assert exc.value.status_code == 410


def test_grace_remaining_is_none_when_not_pending(mock_user):
    assert account_service.grace_remaining(mock_user) is None


def test_grace_remaining_counts_down(mock_user):
    mock_user.deletion_requested_at = datetime.utcnow() - timedelta(days=10)
    remaining = account_service.grace_remaining(mock_user)
    assert remaining is not None
    # ~20 days left, allow a generous fuzz window
    assert 19 * 86400 < remaining.total_seconds() < 21 * 86400


# --- API-level ---


@pytest.mark.asyncio
async def test_api_delete_me_marks_pending_and_logs(
    async_client, override_deps, mock_user, caplog
):
    caplog.set_level(logging.INFO, logger="inrem.audit.account")
    resp = await async_client.request(
        "DELETE",
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["deletion_requested_at"] is not None
    assert body["grace_period_days"] == 30
    assert body["seconds_remaining"] is not None
    assert any(
        r.getMessage() == "account_deletion_requested" for r in caplog.records
    )


@pytest.mark.asyncio
async def test_api_restore_clears_pending(
    async_client, override_deps, mock_user
):
    mock_user.deletion_requested_at = datetime.utcnow() - timedelta(days=1)
    resp = await async_client.post(
        "/api/v1/auth/me/restore",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["deletion_requested_at"] is None
    assert body["seconds_remaining"] is None
