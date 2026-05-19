import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limit import LOGIN_LIMITER
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token
from app.db.session import get_db
from app.repositories import user_repository
from app.schemas.auth import (
    DeletionStatusResponse,
    RefreshRequest,
    Token,
    UserCreate,
    UserResponse,
)
from app.services import account_service, auth_service, AuthServiceError
from app.api.deps import get_current_user
from app.models.user import User
from uuid import UUID

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
        _, access_token, refresh_token = await auth_service.register_user(
            db, user_create
        )
        return Token(access_token=access_token, refresh_token=refresh_token)
    except AuthServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate a user and return an access token.

    OAuth2 password flow (form data: username = email, password).

    **Rate limited** to 5 attempts / minute per `(email, client IP)` —
    brute-force defense. Successful and failed attempts both count;
    legitimate fat-finger users see a 429 with `Retry-After: 60`.
    """
    # IP from X-Forwarded-For when behind a proxy, else direct.
    client_ip = (
        request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )
    LOGIN_LIMITER.check(f"login:{form_data.username.lower()}:{client_ip}")

    result = await auth_service.authenticate_user(db, form_data.username, form_data.password)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    _, access_token, refresh_token = result
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Trade a valid refresh token for a brand-new (access, refresh) pair.

    Refresh **rotation**: the old refresh is rejected on subsequent calls
    only if the token expires — we don't keep a revocation list yet.
    Stateless rotation is sufficient until session theft becomes a real
    concern; at that point add a `refresh_tokens` table keyed by jti.

    Account state is re-checked: deactivated or deletion-pending users
    cannot mint new tokens via this endpoint.
    """
    subject = decode_refresh_token(payload.refresh_token)
    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    try:
        user_id = UUID(subject)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    user = await user_repository.get_user_by_id(db, user_id)
    if user is None or not user.is_active or user.deletion_requested_at is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account no longer eligible",
        )
    return Token(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
    )


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
