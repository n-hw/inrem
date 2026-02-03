"""Signal API endpoints for Guardian Pulse."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.signal import HeartbeatRequest, HeartbeatResponse
from app.services import signal_service

router = APIRouter(prefix="/signal", tags=["signal"])


@router.post("/heartbeat", response_model=HeartbeatResponse, status_code=status.HTTP_200_OK)
async def send_heartbeat(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: HeartbeatRequest | None = None,
):
    """Record a heartbeat signal from the user's device.
    
    This endpoint should be called:
    - When the app comes to foreground
    - Periodically while the app is active
    - On significant user interactions
    
    The server will:
    - Update the user's last_active_at timestamp
    - Record the activity signal for analytics
    """
    signal_type = request.signal_type if request else None
    device_info = request.device_info if request else None
    
    signal, last_active_at = await signal_service.record_heartbeat(
        db=db,
        user_id=current_user.id,
        signal_type=signal_type,
        device_info=device_info,
    )
    
    return HeartbeatResponse(
        success=True,
        last_active_at=last_active_at,
        signal_id=signal.id,
    )
