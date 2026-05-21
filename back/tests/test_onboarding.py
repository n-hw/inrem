"""Tests for PATCH /api/v1/auth/me/onboarding."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_user_no_onboarding():
    return User(
        id=uuid4(),
        email="newuser@inrem.test",
        is_active=True,
        onboarding_completed_at=None,
    )


@pytest.fixture
def mock_user_onboarded():
    ts = datetime(2026, 5, 20, 10, 0, 0)
    return User(
        id=uuid4(),
        email="existing@inrem.test",
        is_active=True,
        onboarding_completed_at=ts,
    )


@pytest.fixture
def override_no_onboarding(mock_user_no_onboarding):
    db_mock = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: mock_user_no_onboarding
    app.dependency_overrides[get_db] = lambda: db_mock
    yield db_mock
    app.dependency_overrides = {}


@pytest.fixture
def override_onboarded(mock_user_onboarded):
    db_mock = AsyncMock()
    app.dependency_overrides[get_current_user] = lambda: mock_user_onboarded
    app.dependency_overrides[get_db] = lambda: db_mock
    yield db_mock
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_complete_onboarding_sets_timestamp(async_client, override_no_onboarding, mock_user_no_onboarding):
    """First call: sets onboarding_completed_at and returns it."""
    resp = await async_client.patch(
        "/api/v1/auth/me/onboarding",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "onboarding_completed_at" in body
    assert body["onboarding_completed_at"] is not None
    # User object was mutated
    assert mock_user_no_onboarding.onboarding_completed_at is not None


@pytest.mark.asyncio
async def test_complete_onboarding_idempotent(async_client, override_onboarded, mock_user_onboarded):
    """Second call: returns existing timestamp unchanged."""
    original_ts = mock_user_onboarded.onboarding_completed_at
    resp = await async_client.patch(
        "/api/v1/auth/me/onboarding",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["onboarding_completed_at"] == original_ts.isoformat()
    # Timestamp not changed
    assert mock_user_onboarded.onboarding_completed_at == original_ts


@pytest.mark.asyncio
async def test_complete_onboarding_requires_auth(async_client):
    """No token → 401."""
    resp = await async_client.patch("/api/v1/auth/me/onboarding")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_includes_onboarding_field(async_client, override_no_onboarding, mock_user_no_onboarding):
    """GET /auth/me must include onboarding_completed_at."""
    resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer test"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "onboarding_completed_at" in body
