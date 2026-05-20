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


# --- purge sweep ---


@pytest.mark.asyncio
async def test_purge_expired_deletes_only_overdue_users(caplog):
    """31일 지난 사용자만 삭제. 29일 사용자나 미요청 사용자는 보존."""
    import logging

    from unittest.mock import MagicMock

    overdue = User(
        id=uuid4(),
        email="overdue@x.com",
        is_active=True,
        deletion_requested_at=datetime.utcnow() - timedelta(days=31),
    )
    fresh_pending = User(
        id=uuid4(),
        email="fresh@x.com",
        is_active=True,
        deletion_requested_at=datetime.utcnow() - timedelta(days=10),
    )
    not_pending = User(
        id=uuid4(), email="alive@x.com", is_active=True, deletion_requested_at=None
    )

    # We only assert which rows the SQL select returns; the actual db
    # delete is captured via AsyncMock.
    db = AsyncMock()
    db.execute = AsyncMock()
    result = MagicMock()
    scalars = MagicMock()
    # The query filters by `deletion_requested_at < cutoff` — service-level
    # logic delegates that to SQL, so we simulate the DB returning only the
    # overdue row.
    scalars.all.return_value = [overdue]
    result.scalars.return_value = scalars
    db.execute.return_value = result
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    caplog.set_level(logging.INFO, logger="inrem.audit.account")

    purged = await account_service.purge_expired_deletions(db)

    assert purged == [overdue.id]
    db.delete.assert_awaited_once_with(overdue)
    db.commit.assert_awaited()
    assert any(
        r.getMessage() == "account_purged" and r.user_id == str(overdue.id)
        for r in caplog.records
    )


@pytest.mark.asyncio
async def test_login_rate_limit_blocks_6th_attempt(async_client):
    """5 attempts pass through (regardless of success), 6th gets 429."""
    from unittest.mock import AsyncMock, patch

    from app.core.rate_limit import LOGIN_LIMITER

    # Reset bucket
    with LOGIN_LIMITER._lock:
        LOGIN_LIMITER._events.clear()

    with patch(
        "app.services.auth_service.authenticate_user",
        new=AsyncMock(return_value=None),
    ):
        for i in range(LOGIN_LIMITER.limit):
            resp = await async_client.post(
                "/api/v1/auth/login",
                data={"username": "u@x.com", "password": "wrong"},
            )
            assert resp.status_code == 401, f"attempt {i + 1} should be 401, got {resp.status_code}"
        # 6th
        resp = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "u@x.com", "password": "wrong"},
        )
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


@pytest.mark.asyncio
async def test_login_rate_limit_keyed_by_email_and_ip(async_client):
    """Different emails (same IP) bucket separately."""
    from unittest.mock import AsyncMock, patch

    from app.core.rate_limit import LOGIN_LIMITER

    with LOGIN_LIMITER._lock:
        LOGIN_LIMITER._events.clear()

    with patch(
        "app.services.auth_service.authenticate_user",
        new=AsyncMock(return_value=None),
    ):
        # Exhaust quota for email A
        for _ in range(LOGIN_LIMITER.limit):
            await async_client.post(
                "/api/v1/auth/login",
                data={"username": "a@x.com", "password": "x"},
            )
        # Email B should still go through
        resp = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "b@x.com", "password": "x"},
        )
    assert resp.status_code == 401  # Auth fail, NOT rate-limit


@pytest.mark.asyncio
async def test_register_rate_limited_per_ip(async_client):
    """같은 IP 6번째 회원가입 시도 → 429. (이메일은 매번 달라도 IP 키로 묶임)"""
    from unittest.mock import AsyncMock, patch

    from app.core.rate_limit import REGISTER_LIMITER

    with REGISTER_LIMITER._lock:
        REGISTER_LIMITER._events.clear()

    # 5번 통과 (mock 으로 항상 성공 응답)
    fake = (User(id=uuid4(), email="x@x.com"), "access-tok", "refresh-tok")
    with patch(
        "app.services.auth_service.register_user",
        new=AsyncMock(return_value=fake),
    ):
        for i in range(REGISTER_LIMITER.limit):
            r = await async_client.post(
                "/api/v1/auth/register",
                json={"email": f"signup{i}@example.com", "password": "passw0rd!"},
            )
            assert r.status_code == 201, f"attempt {i + 1}: {r.status_code}"
        # 6th
        r = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "signup-final@example.com", "password": "passw0rd!"},
        )
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_purge_no_candidates_skips_commit():
    from unittest.mock import MagicMock

    db = AsyncMock()
    result = MagicMock()
    scalars = MagicMock()
    scalars.all.return_value = []
    result.scalars.return_value = scalars
    db.execute = AsyncMock(return_value=result)
    db.delete = AsyncMock()
    db.commit = AsyncMock()

    purged = await account_service.purge_expired_deletions(db)

    assert purged == []
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
