from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import UserCreate


class AuthServiceError(Exception):
    """Custom exception for auth service errors."""
    pass


def _issue_tokens(user_id: str) -> tuple[str, str]:
    """Mint a fresh (access, refresh) pair for `user_id`."""
    return create_access_token(subject=user_id), create_refresh_token(subject=user_id)


async def register_user(
    db: AsyncSession, user_create: UserCreate
) -> tuple[User, str, str]:
    """Register a new user.

    Returns `(user, access_token, refresh_token)`.
    Raises `AuthServiceError` if the email is already registered.
    """
    existing_user = await user_repository.get_user_by_email(db, user_create.email)
    if existing_user:
        raise AuthServiceError("Email already registered")

    user = await user_repository.create_user(db, user_create)
    access, refresh = _issue_tokens(str(user.id))
    return user, access, refresh


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> tuple[User, str, str] | None:
    """Authenticate by (email, password). Returns `(user, access, refresh)` or None.

    Returns None for any auth-failure shape (no enumeration leak).
    """
    user = await user_repository.get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    # PIPA: 삭제 요청 후 grace 기간 중에도 새 로그인은 차단한다.
    # 기존 세션은 토큰이 살아있는 동안 /me/restore 로 복구 가능.
    if user.deletion_requested_at is not None:
        return None

    access, refresh = _issue_tokens(str(user.id))
    return user, access, refresh
