from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_config import UserConfig
from app.models.timer_status import TimerStatus

async def get_user_config(db: AsyncSession, user_id: UUID) -> UserConfig | None:
    """Fetch user config by user ID."""
    result = await db.execute(select(UserConfig).where(UserConfig.user_id == user_id))
    return result.scalar_one_or_none()

async def create_user_config(db: AsyncSession, config: UserConfig) -> UserConfig:
    """Create a new user config."""
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config

async def get_timer_status(db: AsyncSession, user_id: UUID) -> TimerStatus | None:
    """Fetch timer status by user ID."""
    result = await db.execute(select(TimerStatus).where(TimerStatus.user_id == user_id))
    return result.scalar_one_or_none()

async def create_timer_status(db: AsyncSession, status: TimerStatus) -> TimerStatus:
    """Create a new timer status."""
    db.add(status)
    await db.commit()
    await db.refresh(status)
    return status

async def update_timer_status(db: AsyncSession, status: TimerStatus) -> TimerStatus:
    """Update existing timer status."""
    # Assuming 'status' object is already tracked by the session
    await db.commit()
    await db.refresh(status)
    return status
