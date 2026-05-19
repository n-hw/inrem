"""Tests for the Settings API — specifically the paywall click logger."""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="user@inrem.test", is_active=True)


@pytest.fixture
def override_deps(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    yield
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_upsell_click_logs_and_returns_ok(
    async_client, override_deps, mock_user, caplog
):
    caplog.set_level(logging.INFO, logger="inrem.upsell")
    resp = await async_client.post(
        "/api/v1/settings/upsell/click",
        headers={"Authorization": "Bearer test"},
        json={"feature": "family_share", "surface": "home"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"success": True, "feature": "family_share"}
    assert any("upsell_click" in r.getMessage() for r in caplog.records)


@pytest.mark.asyncio
async def test_upsell_click_rejects_unknown_feature(
    async_client, override_deps
):
    resp = await async_client.post(
        "/api/v1/settings/upsell/click",
        headers={"Authorization": "Bearer test"},
        json={"feature": "totally_made_up"},
    )
    assert resp.status_code == 422
