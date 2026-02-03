"""Schemas for device/FCM token management."""

from pydantic import BaseModel


class RegisterDeviceRequest(BaseModel):
    """Request to register a device's FCM token."""
    fcm_token: str


class RegisterDeviceResponse(BaseModel):
    """Response after registering device token."""
    success: bool = True
    message: str = "Device registered successfully"
