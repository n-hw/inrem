"""Signal API endpoints for Guardian Pulse."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.rate_limit import HEARTBEAT_LIMITER
from app.models.user import User
from app.schemas.signal import (
    HeartbeatRequest,
    HeartbeatResponse,
    StatusResponse,
)
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
    # Rate-limit: 분당 60회 (1초 1회). 정상 흐름은 app_open + ~30s 주기 →
    # 충분히 여유 있지만 무한 reset 공격은 차단.
    HEARTBEAT_LIMITER.check(f"hb:{current_user.id}")

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


@router.get("/status", response_model=StatusResponse)
async def get_status(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Read-only Pulse status snapshot — **no side effects**.

    HomeScreen calls this on a polling interval so the timer reflects
    activity from other devices without minting yet another heartbeat
    signal.
    """
    return StatusResponse(
        last_active_at=current_user.last_active_at,
        deletion_requested_at=current_user.deletion_requested_at,
    )
