"""Schemas for Guardian Management API."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr


class GuardianBase(BaseModel):
    """Base schema for Guardian."""
    pass


class CreateInvitationResponse(BaseModel):
    """Response when creating an invitation code."""
    code: str
    expires_at: datetime


class AcceptInvitationRequest(BaseModel):
    """Request to accept an invitation."""
    code: str


class GuardianResponse(GuardianBase):
    """Guardian details response."""
    id: UUID
    email: EmailStr
    is_active: bool
    # We can add more fields like phone number later if needed

    class Config:
        from_attributes = True


class GuardianListResponse(BaseModel):
    """List of guardians."""
    guardians: list[GuardianResponse]


class WardListResponse(BaseModel):
    """List of wards."""
    wards: list[GuardianResponse]
