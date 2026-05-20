"""Schemas for Guardian Pulse signal endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.activity_signal import SignalType


class HeartbeatRequest(BaseModel):
    """Request body for heartbeat endpoint.
    
    Optional - can be used to provide additional context.
    """
    signal_type: SignalType = SignalType.HEARTBEAT
    device_info: str | None = None


class HeartbeatResponse(BaseModel):
    """Response from heartbeat endpoint."""
    success: bool = True
    last_active_at: datetime
    signal_id: UUID


class ActivitySignalResponse(BaseModel):
    """Response model for activity signal data."""
    id: UUID
    user_id: UUID
    signal_type: SignalType
    timestamp: datetime
    device_info: str | None = None

    model_config = ConfigDict(from_attributes=True)


class StatusResponse(BaseModel):
    """Read-only Pulse status snapshot — no side effects.

    HomeScreen uses this for polling so it can refresh the timer
    without registering yet another activity signal.
    """
    last_active_at: datetime | None
    deletion_requested_at: datetime | None
