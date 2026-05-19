"""JWT refresh token tests — type isolation + /auth/refresh endpoint."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)
from app.db.session import get_db
from app.main import app
from app.models.user import User


# --- type isolation ---


def test_access_token_decodes_only_as_access():
    """A token minted as `access` must decode via access path, not refresh."""
    tok = create_access_token("user-1")
    assert decode_access_token(tok) == "user-1"
    assert decode_refresh_token(tok) is None  # cross-type rejected


def test_refresh_token_decodes_only_as_refresh():
    tok = create_refresh_token("user-1")
    assert decode_refresh_token(tok) == "user-1"
    assert decode_access_token(tok) is None


def test_garbage_token_rejected_by_both():
    assert decode_access_token("garbage.token.here") is None
    assert decode_refresh_token("garbage.token.here") is None


# --- /auth/refresh endpoint ---


@pytest.fixture
def active_user():
    return User(
        id=uuid4(),
        email="active@inrem.test",
        is_active=True,
        deletion_requested_at=None,
        password_hash="x",
    )


@pytest.mark.asyncio
async def test_refresh_endpoint_mints_new_pair(async_client, active_user):
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        with patch(
            "app.repositories.user_repository.get_user_by_id",
            new=AsyncMock(return_value=active_user),
        ):
            refresh = create_refresh_token(str(active_user.id))
            resp = await async_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh},
            )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body and "refresh_token" in body
        # Newly issued access decodes correctly.
        assert decode_access_token(body["access_token"]) == str(active_user.id)
        # New refresh decodes as a refresh-type token belonging to the same user.
        assert decode_refresh_token(body["refresh_token"]) == str(active_user.id)
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_refresh_endpoint_rejects_access_token_as_refresh(async_client):
    """Sending an access token to /auth/refresh must 401."""
    access = create_access_token(str(uuid4()))
    resp = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access},  # wrong type
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_endpoint_rejects_pending_deletion_user(
    async_client, active_user
):
    active_user.deletion_requested_at = datetime.utcnow() - timedelta(days=1)
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    try:
        with patch(
            "app.repositories.user_repository.get_user_by_id",
            new=AsyncMock(return_value=active_user),
        ):
            refresh = create_refresh_token(str(active_user.id))
            resp = await async_client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": refresh},
            )
        assert resp.status_code == 401
    finally:
        app.dependency_overrides = {}
