"""Pulse API endpoints for Guardian Pulse."""

from typing import Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.pulse_event import PulseEvent, PulseStatus
from app.schemas.pulse import PulseResponseRequest, PulseResponseResponse

router = APIRouter(prefix="/pulse", tags=["pulse"])


@router.post("/respond", response_model=PulseResponseResponse, status_code=status.HTTP_200_OK)
async def respond_to_pulse(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: PulseResponseRequest | None = None,
):
    """Respond to a soft check-in notification.
    
    User confirms they are okay.
    1. Updates any OPEN pulse events to RESOLVED.
    2. Updates user's last_active_at.
    """
    # 1. Update User's last_active_at
    now = datetime.utcnow()
    
    current_user.last_active_at = now
    db.add(current_user)
    
    # 2. Find and resolve open pulse events
    query = select(PulseEvent).where(
        and_(
            PulseEvent.user_id == current_user.id,
            PulseEvent.status == PulseStatus.OPEN,
        )
    )
    
    if request and request.event_id:
        query = query.where(PulseEvent.id == request.event_id)
        
    result = await db.execute(query)
    events = result.scalars().all()
    
    resolved_count = 0
    for event in events:
        event.status = PulseStatus.RESOLVED
        event.resolved_at = now
        event.resolved_by = current_user.id
        event.resolution_method = "user_response"
        resolved_count += 1
    
    await db.commit()
    
    return PulseResponseResponse(
        success=True,
        message=f"Status confirmed. {resolved_count} event(s) resolved.",
        status=PulseStatus.RESOLVED
    )
