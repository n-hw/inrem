from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration request."""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for token response.

    `access_token` 은 짧은 lifetime (분 단위), `refresh_token` 은 긴
    lifetime (일 단위). 클라이언트는 access 가 만료되면 refresh 로
    `POST /auth/refresh` 를 호출해 새 쌍을 받는다.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenData(BaseModel):
    """Schema for decoded token payload."""
    user_id: UUID | None = None


class UserResponse(BaseModel):
    """Schema for user response (no password)."""
    id: UUID
    email: str
    is_active: bool
    onboarding_completed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class OnboardingResponse(BaseModel):
    onboarding_completed_at: str


class DeletionStatusResponse(BaseModel):
    """Status returned after account deletion / restore actions."""
    deletion_requested_at: str | None
    grace_period_days: int
    seconds_remaining: int | None
