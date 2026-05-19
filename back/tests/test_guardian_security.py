"""Security-focused tests for the Guardian flow.

- Invitation rate-limit (5/hour per user) → 6th call yields 429.
- Audit logger ('inrem.audit.guardian') receives events on
  invitation create / accept / remove.
- DB-level unique constraint on (ward_id, guardian_id).
"""
from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.user import User


@pytest.fixture
def mock_user():
    return User(id=uuid4(), email="ward@inrem.test", is_active=True)


@pytest.fixture
def override_deps(mock_user):
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: AsyncMock()
    yield
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_guardian_invite_audit_logged(
    async_client, override_deps, mock_user, caplog
):
    from app.core.rate_limit import GUARDIAN_INVITE_LIMITER

    with GUARDIAN_INVITE_LIMITER._lock:
        GUARDIAN_INVITE_LIMITER._events.clear()

    caplog.set_level(logging.INFO, logger="inrem.audit.guardian")
    with patch(
        "app.services.guardian_service.create_invitation_code",
        new=AsyncMock(return_value="CODE-1"),
    ):
        resp = await async_client.post(
            "/api/v1/guardian/invite",
            headers={"Authorization": "Bearer test"},
        )
    assert resp.status_code == 201
    assert any(
        r.getMessage() == "guardian_invitation_created" for r in caplog.records
    )


@pytest.mark.asyncio
async def test_guardian_invite_rate_limited(async_client, override_deps):
    from app.core.rate_limit import GUARDIAN_INVITE_LIMITER

    with GUARDIAN_INVITE_LIMITER._lock:
        GUARDIAN_INVITE_LIMITER._events.clear()

    with patch(
        "app.services.guardian_service.create_invitation_code",
        new=AsyncMock(return_value="CODE-N"),
    ):
        # 5 allowed
        for _ in range(GUARDIAN_INVITE_LIMITER.limit):
            r = await async_client.post(
                "/api/v1/guardian/invite",
                headers={"Authorization": "Bearer test"},
            )
            assert r.status_code == 201
        # 6th
        r = await async_client.post(
            "/api/v1/guardian/invite",
            headers={"Authorization": "Bearer test"},
        )
    assert r.status_code == 429


@pytest.mark.asyncio
async def test_guardian_accept_audit_logged(
    async_client, override_deps, caplog
):
    caplog.set_level(logging.INFO, logger="inrem.audit.guardian")
    with patch(
        "app.services.guardian_service.accept_invitation",
        new=AsyncMock(return_value=None),
    ):
        resp = await async_client.post(
            "/api/v1/guardian/accept",
            headers={"Authorization": "Bearer test"},
            json={"code": "CODE-1"},
        )
    assert resp.status_code == 200
    assert any(
        r.getMessage() == "guardian_invitation_accepted" for r in caplog.records
    )


@pytest.mark.asyncio
async def test_guardian_remove_audit_logged(
    async_client, override_deps, caplog
):
    caplog.set_level(logging.INFO, logger="inrem.audit.guardian")
    with patch(
        "app.services.guardian_service.remove_guardian",
        new=AsyncMock(return_value=True),
    ):
        resp = await async_client.delete(
            f"/api/v1/guardian/{uuid4()}",
            headers={"Authorization": "Bearer test"},
        )
    assert resp.status_code == 204
    assert any(r.getMessage() == "guardian_removed" for r in caplog.records)


@pytest.mark.asyncio
async def test_guardian_unique_constraint_blocks_duplicate():
    """ORM model now declares UniqueConstraint(ward_id, guardian_id)."""
    from sqlalchemy import JSON
    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from sqlalchemy.exc import IntegrityError

    from app.db.base import Base
    from app.models.guardian import Guardian
    from app.models.record import Record

    orig_type = Record.__table__.c.metadata_info.type
    Record.__table__.c.metadata_info.type = JSON()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as s:
            ward = User(id=uuid4(), email="w@x.com", password_hash="x", is_active=True)
            guardian = User(id=uuid4(), email="g@x.com", password_hash="x", is_active=True)
            s.add_all([ward, guardian])
            await s.flush()
            s.add(Guardian(id=uuid4(), ward_id=ward.id, guardian_id=guardian.id))
            await s.commit()
            s.add(Guardian(id=uuid4(), ward_id=ward.id, guardian_id=guardian.id))
            with pytest.raises(IntegrityError):
                await s.commit()
    finally:
        Record.__table__.c.metadata_info.type = orig_type
        await engine.dispose()
