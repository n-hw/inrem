"""Account lifecycle service — deletion request, grace period, restore.

PIPA (개인정보보호법) 잊혀질 권리 구현. PRD §6 NFR:
"사용자 삭제 요청 시 30일 grace → 영구 삭제."

Flow:
1. User calls `DELETE /api/v1/auth/me` → `request_deletion()`
   - Stamps `deletion_requested_at = now()` and `is_active = False`.
   - User can no longer log in (login flow checks `is_active`).
2. Within 30 days, user can `POST /api/v1/auth/me/restore` to undo.
   - Clears `deletion_requested_at`, restores `is_active = True`.
3. After 30 days, a scheduled purger deletes the row + cascaded data
   (out of scope for this service — handled by `scheduler.py`).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

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
