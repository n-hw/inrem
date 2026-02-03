"""Schemas for Pulse API endpoints."""

from uuid import UUID
from pydantic import BaseModel
from app.models.pulse_event import PulseStatus


class PulseResponseRequest(BaseModel):
    """Request to respond to a soft check-in."""
    event_id: UUID | None = None  # Optional: if provided, validates specific event


class PulseResponseResponse(BaseModel):
    """Response after user confirms they are okay."""
    success: bool = True
    message: str = "Analysis confirmed. Timer reset."
    status: PulseStatus
