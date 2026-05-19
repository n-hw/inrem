from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import timer_repository
from app.models.timer_status import TimerStatus, TimerState
from app.models.user_config import UserConfig

async def reset_timer(db: AsyncSession, user_id: UUID) -> TimerStatus:
    """
    Reset the timer for the user.
    Calculates new deadline based on UserConfig.
    Updates TimerStatus.
    """
    # 1. Get Config
    config = await timer_repository.get_user_config(db, user_id)
    if not config:
        # Create default config if missing
        config = UserConfig(user_id=user_id)
        config = await timer_repository.create_user_config(db, config)
    
    if not config.is_active:
         raise HTTPException(status_code=400, detail="Timer is disabled for this user")

    # 2. Calculate new deadline
    # Use naive UTC to match database convention (datetime.utcnow)
    now = datetime.utcnow()
    deadline = now + timedelta(seconds=config.period)

    # 3. Get or Create Status
    status = await timer_repository.get_timer_status(db, user_id)
    if not status:
        status = TimerStatus(
            user_id=user_id,
            last_check_in=now,
            deadline_timestamp=deadline,
            status=TimerState.ACTIVE
        )
        status = await timer_repository.create_timer_status(db, status)
    else:
        status.last_check_in = now
        status.deadline_timestamp = deadline
        status.status = TimerState.ACTIVE
        status = await timer_repository.update_timer_status(db, status)
        
    return status
