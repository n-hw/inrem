from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.timer import TimerStatusResponse
from app.services import timer_service

router = APIRouter(prefix="/timer", tags=["timer"])

@router.post("/reset", response_model=TimerStatusResponse, status_code=status.HTTP_200_OK)
async def reset_timer(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reset the dead man's timer.
    Updates the last_check_in time and recalculates the deadline.
    """
    return await timer_service.reset_timer(db, current_user.id)
