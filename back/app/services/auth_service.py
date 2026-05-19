from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import UserCreate
from app.repositories import user_repository
from app.core.security import verify_password, create_access_token


class AuthServiceError(Exception):
    """Custom exception for auth service errors."""
    pass


async def register_user(db: AsyncSession, user_create: UserCreate) -> tuple[User, str]:
    """Register a new user.
    
    Args:
        db: Database session.
        user_create: User creation data.
    
    Returns:
        Tuple of (created user, access token).
    
    Raises:
        AuthServiceError: If email already registered.
    """
    existing_user = await user_repository.get_user_by_email(db, user_create.email)
    if existing_user:
        raise AuthServiceError("Email already registered")
    
    user = await user_repository.create_user(db, user_create)
    access_token = create_access_token(subject=str(user.id))
    return user, access_token


async def authenticate_user(db: AsyncSession, email: str, password: str) -> tuple[User, str] | None:
    """Authenticate a user with email and password.
    
    Args:
        db: Database session.
        email: User's email.
        password: Plain text password.
    
    Returns:
        Tuple of (user, access token) if authenticated, None otherwise.
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

    access_token = create_access_token(subject=str(user.id))
    return user, access_token
