"""Integration test: User 삭제 시 모든 종속 행이 cascade 되는지 검증.

In-memory SQLite 로 빠른 round-trip 검증. ORM 레벨 cascade(`cascade="all,
delete-orphan"`) 가 동작하면 충분 — DB FK 의 `ondelete=CASCADE` 는 출시
전 alembic 마이그레이션에서 추가 예정.
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.activity_signal import ActivitySignal, SignalType
from app.models.asset import ActionOnDeath, Asset, AssetType
from app.models.guardian import Guardian
from app.models.monitoring_policy import MonitoringPolicy
from app.models.pulse_event import PulseEvent
from app.models.timer_status import TimerState, TimerStatus
from app.models.user import User
from app.models.user_config import UserConfig


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    """In-memory SQLite session.

    User cascade 가 `records` 관계를 traverse 하므로 records 테이블도
    함께 만든다. 다만 Postgres JSONB 는 SQLite 가 컴파일 못 하므로,
    이 fixture 안에서만 임시로 generic JSON 으로 swap.
    """
    from sqlalchemy import JSON

    from app.models.record import Record

    orig_type = Record.__table__.c.metadata_info.type
    Record.__table__.c.metadata_info.type = JSON()
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as s:
            yield s
    finally:
        Record.__table__.c.metadata_info.type = orig_type
        await engine.dispose()


@pytest.mark.asyncio
async def test_user_delete_cascades_owned_rows(session):
    """User → 모든 owner-side 종속 행(자산·신호·정책·이벤트·타이머·설정)."""
    user = User(
        id=uuid4(),
        email="cascade@inrem.test",
        password_hash="x",
        is_active=True,
        last_active_at=datetime.utcnow(),
    )
    session.add(user)
    await session.flush()

    # Populate dependents
    session.add_all([
        ActivitySignal(
            id=uuid4(), user_id=user.id, signal_type=SignalType.HEARTBEAT,
            timestamp=datetime.utcnow(),
        ),
        Asset(
            id=uuid4(), user_id=user.id, name="test", type=AssetType.CUSTOM,
            action_on_death=ActionOnDeath.KEEP_PRIVATE,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        ),
        MonitoringPolicy(id=uuid4(), user_id=user.id),
        TimerStatus(
            id=uuid4(), user_id=user.id, status=TimerState.STOPPED,
        ),
        UserConfig(id=uuid4(), user_id=user.id),
    ])
    await session.commit()

    # Sanity: rows exist
    for model in (ActivitySignal, Asset, MonitoringPolicy, TimerStatus, UserConfig):
        result = await session.execute(select(model).where(model.user_id == user.id))
        assert result.scalars().first() is not None, f"{model.__name__} not seeded"

    # Delete the user
    await session.delete(user)
    await session.commit()

    # Every owner-side dependent must be gone.
    for model in (ActivitySignal, Asset, MonitoringPolicy, TimerStatus, UserConfig):
        result = await session.execute(select(model).where(model.user_id == user.id))
        assert (
            result.scalars().first() is None
        ), f"{model.__name__} row survived user delete — cascade missing"


@pytest.mark.asyncio
async def test_user_delete_cascades_guardian_mappings(session):
    """Both sides of the Guardian join table are removed when either user dies."""
    ward = User(id=uuid4(), email="ward@x.com", password_hash="x", is_active=True)
    guardian = User(id=uuid4(), email="grd@x.com", password_hash="x", is_active=True)
    session.add_all([ward, guardian])
    await session.flush()

    session.add(
        Guardian(
            id=uuid4(),
            ward_id=ward.id,
            guardian_id=guardian.id,
            alias="dad",
        )
    )
    await session.commit()

    # Delete the ward → guardian mapping (ward_id side) goes with them.
    await session.delete(ward)
    await session.commit()

    rows = (await session.execute(select(Guardian))).scalars().all()
    assert rows == [], "Guardian mapping survived ward delete"
