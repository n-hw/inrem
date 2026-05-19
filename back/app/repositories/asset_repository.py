"""Repository layer for Heritage Box assets."""
from __future__ import annotations

from typing import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.asset import Asset


async def list_by_user(
    db: AsyncSession,
    user_id: UUID,
    *,
    type_filter: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> Sequence[Asset]:
    """Return paginated assets owned by `user_id`, newest first.

    `search` does a case-insensitive substring match on `name`.
    """
    stmt = (
        select(Asset)
        .where(Asset.user_id == user_id)
        .order_by(Asset.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if type_filter:
        stmt = stmt.where(Asset.type == type_filter)
    if search:
        stmt = stmt.where(Asset.name.ilike(f"%{search}%"))
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_by_id(
    db: AsyncSession, asset_id: UUID, *, user_id: UUID | None = None
) -> Asset | None:
    """Fetch a single asset. If `user_id` is given, scope to owner."""
    stmt = select(Asset).where(Asset.id == asset_id)
    if user_id is not None:
        stmt = stmt.where(Asset.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create(db: AsyncSession, asset: Asset) -> Asset:
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return asset


async def update(db: AsyncSession, asset: Asset) -> Asset:
    """Persist changes made on a session-tracked Asset."""
    await db.commit()
    await db.refresh(asset)
    return asset


async def delete(db: AsyncSession, asset: Asset) -> None:
    await db.delete(asset)
    await db.commit()


async def count_by_user(db: AsyncSession, user_id: UUID) -> int:
    stmt = select(func.count(Asset.id)).where(Asset.user_id == user_id)
    result = await db.execute(stmt)
    return int(result.scalar_one())


async def count_grouped(
    db: AsyncSession, user_id: UUID, column
) -> dict[str, int]:
    """Aggregate count grouped by `column`, scoped to user."""
    stmt = (
        select(column, func.count(Asset.id))
        .where(Asset.user_id == user_id)
        .group_by(column)
    )
    result = await db.execute(stmt)
    out: dict[str, int] = {}
    for key, count in result.all():
        # SQLAlchemy may return Enum instances or strings depending on dialect
        out[getattr(key, "value", key)] = int(count)
    return out
