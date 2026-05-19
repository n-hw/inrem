import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import (
    DeletionStatusResponse,
    Token,
    UserCreate,
    UserResponse,
)
from app.services import account_service, auth_service, AuthServiceError
from app.api.deps import get_current_user
from app.models.user import User

audit_logger = logging.getLogger("inrem.audit.account")

router = APIRouter(prefix="/auth", tags=["auth"])


def _deletion_status(user: User) -> DeletionStatusResponse:
    requested = user.deletion_requested_at
    remaining = account_service.grace_remaining(user)
    return DeletionStatusResponse(
        deletion_requested_at=requested.isoformat() if requested else None,
        grace_period_days=account_service.GRACE_PERIOD_DAYS,
        seconds_remaining=int(remaining.total_seconds()) if remaining else None,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_create: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user.
    
    Args:
        user_create: User registration data (email, password).
        db: Database session.
    
    Returns:
        Access token for the newly registered user.
    """
    try:
        _, access_token = await auth_service.register_user(db, user_create)
        return Token(access_token=access_token)
    except AuthServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate a user and return an access token.
    
    Uses OAuth2 password flow (form data: username, password).
    Note: 'username' field is used for email.
    
    Args:
        form_data: OAuth2 form with username (email) and password.
        db: Database session.
    
    Returns:
        Access token for authenticated user.
    """
    result = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _, access_token = result
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get the currently authenticated user's information.

    Args:
        current_user: The authenticated user (from JWT).

    Returns:
        User information.
    """
    return current_user


@router.delete("/me", response_model=DeletionStatusResponse)
async def request_account_deletion(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Request account deletion (PIPA 잊혀질 권리 / PRD §6 NFR).

    Marks the account as pending deletion and deactivates login. The
    actual data purge runs after a **30-day grace period**, during
    which the user may call `POST /auth/me/restore` to undo.

    This endpoint is idempotent — calling it again on a pending
    account is a no-op and returns the same status.
    """
    user = await account_service.request_deletion(db, user=current_user)
    audit_logger.info(
        "account_deletion_requested",
        extra={
            "user_id": str(user.id),
            "requested_at": user.deletion_requested_at.isoformat(),
        },
    )
    return _deletion_status(user)


@router.post("/me/restore", response_model=DeletionStatusResponse)
async def restore_account(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Cancel a pending deletion if still inside the grace period.

    Returns 410 if the grace period has already elapsed (account
    purge may have run; restore is no longer possible).
    """
    user = await account_service.restore(db, user=current_user)
    audit_logger.info(
        "account_deletion_restored",
        extra={"user_id": str(user.id)},
    )
    return _deletion_status(user)
