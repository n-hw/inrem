"""Service for recording user activity signals."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update

from app.models.user import User
from app.models.activity_signal import ActivitySignal, SignalType


async def record_heartbeat(
    db: AsyncSession,
    user_id: UUID,
    signal_type: SignalType = SignalType.HEARTBEAT,
    device_info: str | None = None,
) -> tuple[ActivitySignal, datetime]:
    """Record a heartbeat signal and update user's last_active_at.
    
    Args:
        db: Database session.
        user_id: ID of the user sending the heartbeat.
        signal_type: Type of activity signal.
        device_info: Optional device information.
        
    Returns:
        Tuple of (created ActivitySignal, updated last_active_at timestamp).
    """
    now = datetime.utcnow()
    
    # Create activity signal record
    signal = ActivitySignal(
        user_id=user_id,
        signal_type=signal_type,
        timestamp=now,
        device_info=device_info,
    )
    db.add(signal)
    
    # Update user's last_active_at
    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(last_active_at=now)
    )
    
    await db.commit()
    await db.refresh(signal)
    
    return signal, now


async def get_user_signals(
    db: AsyncSession,
    user_id: UUID,
    limit: int = 10,
) -> list[ActivitySignal]:
    """Get recent activity signals for a user.
    
    Args:
        db: Database session.
        user_id: ID of the user.
        limit: Maximum number of signals to return.
        
    Returns:
        List of recent ActivitySignal records.
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(ActivitySignal)
        .where(ActivitySignal.user_id == user_id)
        .order_by(ActivitySignal.timestamp.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
