"""PulseEngine - Inactivity detection and PulseEvent creation.

This module contains the core logic for detecting inactive users
and creating PulseEvents to trigger welfare checks.
"""

from datetime import datetime, time, timedelta
from typing import Sequence
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.monitoring_policy import MonitoringPolicy
from app.models.pulse_event import PulseEvent, PulseStage, PulseStatus
from app.services.notification_service import send_soft_checkin_notification


def is_within_quiet_hours(
    current_time: time,
    quiet_start: time,
    quiet_end: time,
) -> bool:
    """Check if current time is within quiet hours.
    
    Handles overnight ranges (e.g., 23:00 - 07:00).
    
    Args:
        current_time: Current time to check.
        quiet_start: Start of quiet hours (e.g., 23:00).
        quiet_end: End of quiet hours (e.g., 07:00).
        
    Returns:
        True if current_time is within quiet hours.
    """
    if quiet_start <= quiet_end:
        # Normal range (e.g., 09:00 - 17:00)
        return quiet_start <= current_time <= quiet_end
    else:
        # Overnight range (e.g., 23:00 - 07:00)
        return current_time >= quiet_start or current_time <= quiet_end


def is_user_inactive(
    last_active_at: datetime | None,
    threshold_hours: int,
    now: datetime | None = None,
) -> bool:
    """Check if a user is considered inactive based on threshold.
    
    Args:
        last_active_at: User's last activity timestamp.
        threshold_hours: Inactivity threshold in hours.
        now: Current time (defaults to utcnow).
        
    Returns:
        True if user has been inactive longer than threshold.
    """
    if last_active_at is None:
        return True  # Never active = inactive
    
    if now is None:
        now = datetime.utcnow()
    
    inactive_duration = now - last_active_at
    threshold = timedelta(hours=threshold_hours)
    
    return inactive_duration > threshold


async def get_users_to_check(db: AsyncSession) -> Sequence[tuple[User, MonitoringPolicy]]:
    """Get all active users with their monitoring policies.
    
    Returns users who have monitoring enabled and are not deceased.
    """
    result = await db.execute(
        select(User, MonitoringPolicy)
        .join(MonitoringPolicy, User.id == MonitoringPolicy.user_id)
        .where(
            and_(
                User.is_active == True,
                User.is_deceased == False,
                MonitoringPolicy.is_active == True,
            )
        )
    )
    return result.all()


async def has_open_pulse_event(db: AsyncSession, user_id: UUID) -> bool:
    """Check if user already has an open PulseEvent.
    
    Prevents duplicate events for the same inactivity period.
    """
    result = await db.execute(
        select(PulseEvent)
        .where(
            and_(
                PulseEvent.user_id == user_id,
                PulseEvent.status == PulseStatus.OPEN,
            )
        )
        .limit(1)
    )
    return result.scalar_one_or_none() is not None


async def create_pulse_event(
    db: AsyncSession,
    user_id: UUID,
    stage: PulseStage = PulseStage.SOFT_CHECK,
) -> PulseEvent:
    """Create a new PulseEvent for an inactive user.
    
    Args:
        db: Database session.
        user_id: ID of the inactive user.
        stage: Initial escalation stage.
        
    Returns:
        Created PulseEvent.
    """
    now = datetime.utcnow()
    
    event = PulseEvent(
        user_id=user_id,
        status=PulseStatus.OPEN,
        current_stage=stage,
        created_at=now,
        soft_check_sent_at=now if stage == PulseStage.SOFT_CHECK else None,
    )
    
    db.add(event)
    await db.commit()
    await db.refresh(event)
    
    return event


    return created_events


async def check_escalations(db: AsyncSession) -> list[PulseEvent]:
    """Check for open events that need escalation.
    
    Escalates from SOFT_CHECK -> GUARDIAN_ALERT if:
    - Status is OPEN
    - Current stage is SOFT_CHECK
    - Time since soft_check_sent_at > policy.escalation_delay_minutes
    """
    now = datetime.utcnow()
    escalated_events: list[PulseEvent] = []
    
    # query for candidate events
    # We join User and MonitoringPolicy to get escalation settings
    stmt = (
        select(PulseEvent, MonitoringPolicy, User)
        .join(User, PulseEvent.user_id == User.id)
        .join(MonitoringPolicy, User.id == MonitoringPolicy.user_id)
        .where(
            and_(
                PulseEvent.status == PulseStatus.OPEN,
                PulseEvent.current_stage == PulseStage.SOFT_CHECK,
                MonitoringPolicy.escalation_enabled == True,
            )
        )
    )
    
    result = await db.execute(stmt)
    candidates = result.all()
    
    for event, policy, user in candidates:
        if not event.soft_check_sent_at:
            continue
            
        # Check if delay time has passed
        time_since_soft_check = now - event.soft_check_sent_at
        delay_threshold = timedelta(minutes=policy.escalation_delay_minutes)
        
        if time_since_soft_check > delay_threshold:
            # Escalate!
            event.current_stage = PulseStage.GUARDIAN_ALERT
            event.guardian_notified_at = now
            db.add(event)
            escalated_events.append(event)
            
            print(f"[PulseEngine] Escalating event {event.id} for user {user.email}")
            
            # Notify Guardians
            # Need to fetch guardians
            from app.services.guardian_service import get_guardians
            from app.services.notification_service import send_guardian_notification
            
            guardians = await get_guardians(db, user.id)
            if guardians:
               count = await send_guardian_notification(user, guardians, event.id)
               print(f"[PulseEngine] Sent alert to {count} guardians")
            else:
               print(f"[PulseEngine] No guardians found for {user.email}")

    await db.commit()
    return escalated_events


async def run_inactivity_check(db: AsyncSession) -> list[PulseEvent]:
    """Main pulse engine loop - check all users for inactivity.
    
    This should be called periodically by the scheduler.
    
    Returns:
        List of newly created PulseEvents.
    """
    now = datetime.utcnow()
    current_time = now.time()
    created_events: list[PulseEvent] = []
    
    # 1. Check for new inactivity
    users_with_policies = await get_users_to_check(db)
    
    for user, policy in users_with_policies:
        # Skip if within quiet hours
        if is_within_quiet_hours(current_time, policy.quiet_start, policy.quiet_end):
            continue
        
        # Skip if not inactive
        if not is_user_inactive(user.last_active_at, policy.threshold_hours, now):
            continue
        
        # Skip if already has open event
        if await has_open_pulse_event(db, user.id):
            continue
        
        # Create new pulse event
        event = await create_pulse_event(db, user.id)
        created_events.append(event)
        print(f"[PulseEngine] Created event {event.id} for user {user.email}")
        
        # Send Soft Check-in Notification
        if event.current_stage == PulseStage.SOFT_CHECK:
            sent = await send_soft_checkin_notification(user, event.id)
            if sent:
                print(f"[PulseEngine] Sent notification to {user.email}")
            else:
                print(f"[PulseEngine] Failed to send notification to {user.email}")
    
    # 2. Check for escalations
    await check_escalations(db)

    return created_events
