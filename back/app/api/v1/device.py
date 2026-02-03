"""Device management API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.device import RegisterDeviceRequest, RegisterDeviceResponse
from app.services.notification_service import update_fcm_token

router = APIRouter(prefix="/device", tags=["device"])


@router.post("/register", response_model=RegisterDeviceResponse, status_code=status.HTTP_200_OK)
async def register_device(
    request: RegisterDeviceRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Register the device's FCM token for push notifications.
    
    This should be called:
    - After user logs in
    - When FCM token is refreshed
    
    The token is stored and used to send push notifications.
    """
    await update_fcm_token(db, current_user.id, request.fcm_token)
    
    return RegisterDeviceResponse(
        success=True,
        message="Device registered successfully",
    )


@router.delete("/unregister", response_model=RegisterDeviceResponse, status_code=status.HTTP_200_OK)
async def unregister_device(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Unregister the device from push notifications.
    
    This clears the FCM token, preventing further notifications.
    """
    await update_fcm_token(db, current_user.id, None)
    
    return RegisterDeviceResponse(
        success=True,
        message="Device unregistered successfully",
    )
