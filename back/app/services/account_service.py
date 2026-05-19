"""Account lifecycle service — deletion request, grace period, restore, purge.

PIPA (개인정보보호법) 잊혀질 권리 구현. PRD §6 NFR:
"사용자 삭제 요청 시 30일 grace → 영구 삭제."

Flow:
1. User calls `DELETE /api/v1/auth/me` → `request_deletion()`
   - Stamps `deletion_requested_at = now()`.
   - Fresh logins are blocked (auth_service checks the stamp); existing
     sessions still work so the user can restore.
2. Within 30 days, user can `POST /api/v1/auth/me/restore` to undo.
   - Clears `deletion_requested_at`.
3. After 30 days, `purge_expired_deletions()` is invoked by the daily
   `AccountPurgeScheduler` and **hard-deletes** the user row. SQLAlchemy
   cascades handle dependent rows (see model relationships).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

audit_logger = logging.getLogger("inrem.audit.account")

GRACE_PERIOD_DAYS = 30


async def request_deletion(db: AsyncSession, *, user: User) -> User:
    """Mark the user as pending deletion. Idempotent.

    We deliberately leave `is_active` alone so the existing session can
    still call `/me/restore` during the grace period. Fresh logins are
    blocked separately in `auth_service.authenticate_user`.
    """
    if user.deletion_requested_at is None:
        user.deletion_requested_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
    return user


async def restore(db: AsyncSession, *, user: User) -> User:
    """Cancel a pending deletion if still within the grace period."""
    if user.deletion_requested_at is None:
        return user

    if _grace_expired(user.deletion_requested_at):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="삭제 유예 기간이 만료되어 복구할 수 없습니다.",
        )

    user.deletion_requested_at = None
    await db.commit()
    await db.refresh(user)
    return user


def grace_remaining(user: User) -> timedelta | None:
    """Return how long until the account is purged. `None` if not pending."""
    if user.deletion_requested_at is None:
        return None
    deadline = user.deletion_requested_at + timedelta(days=GRACE_PERIOD_DAYS)
    return max(timedelta(0), deadline - datetime.utcnow())


def _grace_expired(requested_at: datetime) -> bool:
    return datetime.utcnow() - requested_at > timedelta(days=GRACE_PERIOD_DAYS)


async def purge_expired_deletions(db: AsyncSession) -> list[UUID]:
    """Hard-delete users whose grace period has elapsed.

    Returns the list of purged user IDs (for logging / metrics). Caller
    is expected to be the scheduled `AccountPurgeScheduler` — but the
    function is idempotent and safe to call manually.

    SQLAlchemy cascades handle dependent rows. If the model relationships
    are missing `cascade="all, delete"` on a side, that table's rows will
    survive; add explicit `delete()` calls here as needed.
    """
    cutoff = datetime.utcnow() - timedelta(days=GRACE_PERIOD_DAYS)
    rows = await db.execute(
        select(User).where(
            User.deletion_requested_at.is_not(None),
            User.deletion_requested_at < cutoff,
        )
    )
    expired: list[User] = list(rows.scalars().all())
    purged_ids: list[UUID] = []

    for user in expired:
        purged_ids.append(user.id)
        # Audit log BEFORE the delete commits — we want a trail even if
        # the commit later fails (the row will still be there for retry).
        audit_logger.info(
            "account_purged",
            extra={
                "user_id": str(user.id),
                "requested_at": user.deletion_requested_at.isoformat(),
                "purged_at": datetime.utcnow().isoformat(),
            },
        )
        await db.delete(user)

    if purged_ids:
        await db.commit()
    return purged_ids
