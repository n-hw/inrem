from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import UserCreate
from app.core.security import get_password_hash


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """Fetch a user by their ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
    """Create a new user with hashed password."""
    hashed_password = get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        password_hash=hashed_password,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
