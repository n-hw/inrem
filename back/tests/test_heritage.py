"""Unit + lightweight integration tests for Heritage Box.

Service tests mock the repository so they don't need a DB.
API tests exercise the FastAPI route surface with dependency overrides.
"""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.asset import ActionOnDeath, Asset, AssetType
from app.models.user import User
from app.schemas.asset import AssetCreate, AssetUpdate
from app.services import asset_service


# --- Fixtures ---


@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="user@inrem.test", is_active=True)


def _make_asset(user_id, **overrides) -> Asset:
    now = datetime.utcnow()
    base = dict(
        id=uuid4(),
        user_id=user_id,
        name="Instagram",
        type=AssetType.SOCIAL_ACCOUNT,
        identifier="@me",
        encrypted_payload=None,
        action_on_death=ActionOnDeath.MEMORIALIZE,
        designated_executor_id=None,
        note=None,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return Asset(**base)


# --- Service tests ---


@pytest.mark.asyncio
async def test_create_asset_encrypts_secret(mock_user):
    db = AsyncMock()
    payload = AssetCreate(
        name="Netflix",
        type=AssetType.SUBSCRIPTION,
        identifier="user@inrem.test",
        action_on_death=ActionOnDeath.DELETE,
        secret="super-secret-password",
    )

    captured: dict = {}

    async def fake_create(_db, asset: Asset):
        captured["asset"] = asset
        asset.id = uuid4()
        asset.created_at = datetime.utcnow()
        asset.updated_at = datetime.utcnow()
        return asset

    with patch(
        "app.repositories.asset_repository.create",
        new=AsyncMock(side_effect=fake_create),
    ), patch(
        "app.core.encryption.EncryptionService.encrypt", return_value="ENC:secret"
    ):
        resp = await asset_service.create_asset(
            db, user_id=mock_user.id, payload=payload
        )

    assert resp.name == "Netflix"
    assert resp.type == AssetType.SUBSCRIPTION
    assert resp.action_on_death == ActionOnDeath.DELETE
    assert resp.has_secret is True
    # response should never leak ciphertext
    assert not hasattr(resp, "encrypted_payload")
    # repository was called with encrypted payload, never the plaintext secret
    saved: Asset = captured["asset"]
    assert saved.encrypted_payload == "ENC:secret"


@pytest.mark.asyncio
async def test_update_asset_clear_secret(mock_user):
    db = AsyncMock()
    existing = _make_asset(mock_user.id, encrypted_payload="ENC:old")

    with patch(
        "app.repositories.asset_repository.get_by_id",
        new=AsyncMock(return_value=existing),
    ), patch(
        "app.repositories.asset_repository.update",
        new=AsyncMock(side_effect=lambda _db, a: a),
    ):
        resp = await asset_service.update_asset(
            db,
            user_id=mock_user.id,
            asset_id=existing.id,
            payload=AssetUpdate(clear_secret=True),
        )

    assert resp.has_secret is False
    assert existing.encrypted_payload is None


@pytest.mark.asyncio
async def test_get_asset_not_found_returns_404(mock_user):
    from fastapi import HTTPException

    db = AsyncMock()
    with patch(
        "app.repositories.asset_repository.get_by_id",
        new=AsyncMock(return_value=None),
    ):
        with pytest.raises(HTTPException) as exc:
            await asset_service.get_asset(
                db, user_id=mock_user.id, asset_id=uuid4()
            )
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_reveal_secret_decrypts(mock_user):
    db = AsyncMock()
    asset = _make_asset(mock_user.id, encrypted_payload="ENC:abc")

    with patch(
        "app.repositories.asset_repository.get_by_id",
        new=AsyncMock(return_value=asset),
    ), patch(
        "app.core.encryption.EncryptionService.decrypt", return_value="plaintext"
    ):
        resp = await asset_service.reveal_secret(
            db, user_id=mock_user.id, asset_id=asset.id
        )

    assert resp.secret == "plaintext"


# --- API tests ---


@pytest.fixture
def override_deps(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    yield
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_api_list_assets(async_client, override_deps, mock_user):
    fake_assets = [
        asset_service._to_response(_make_asset(mock_user.id, name="X")),
        asset_service._to_response(_make_asset(mock_user.id, name="Y")),
    ]
    with patch(
        "app.services.asset_service.list_assets",
        new=AsyncMock(return_value=fake_assets),
    ):
        # Provide Authorization so OAuth2PasswordBearer doesn't 401 us
        resp = await async_client.get(
            "/api/v1/heritage/assets",
            headers={"Authorization": "Bearer test"},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert {item["name"] for item in body} == {"X", "Y"}


@pytest.mark.asyncio
async def test_api_create_asset(async_client, override_deps, mock_user):
    created = asset_service._to_response(_make_asset(mock_user.id, name="Crypto"))

    with patch(
        "app.services.asset_service.create_asset",
        new=AsyncMock(return_value=created),
    ) as svc:
        resp = await async_client.post(
            "/api/v1/heritage/assets",
            headers={"Authorization": "Bearer test"},
            json={
                "name": "Crypto",
                "type": "crypto",
                "action_on_death": "transfer",
                "secret": "seed-phrase",
            },
        )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Crypto"
    assert "encrypted_payload" not in body
    svc.assert_called_once()
