from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Schema for user registration request."""
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Schema for user login request."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for decoded token payload."""
    user_id: UUID | None = None


class UserResponse(BaseModel):
    """Schema for user response (no password)."""
    id: UUID
    email: str
    is_active: bool

    class Config:
        from_attributes = True
