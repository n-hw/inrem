"""Guardian service for managing relationships and invitations.

Handles creating invitation codes, accepting invitations,
and listing/removing guardians.
"""

import logging
import random
import string
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select, delete, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.guardian import Guardian

logger = logging.getLogger(__name__)

# Temporary storage for invitation codes (in-memory for MVP, use Redis later)
# Dict[code, {"user_id": UUID, "expires_at": datetime}]
_invitation_codes = {}


def generate_code(length: int = 6) -> str:
    """Generate a random alphanumeric code."""
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choices(chars, k=length))


async def create_invitation_code(user_id: UUID, expires_minutes: int = 60 * 24) -> str:
    """Create an invitation code for a ward.
    
    Args:
        user_id: ID of the user (ward) inviting a guardian.
        expires_minutes: Code expiration time in minutes (default 24h).
        
    Returns:
        The generated invitation code.
    """
    # Clean up expired codes
    now = datetime.utcnow()
    expired = [k for k, v in _invitation_codes.items() if v["expires_at"] < now]
    for k in expired:
        del _invitation_codes[k]
        
    code = generate_code()
    expiration = now + timedelta(minutes=expires_minutes)
    
    _invitation_codes[code] = {
        "user_id": user_id,
        "expires_at": expiration
    }
    
    logger.info(f"[GuardianService] Created code {code} for user {user_id}")
    return code


async def accept_invitation(db: AsyncSession, guardian_id: UUID, code: str) -> Guardian:
    """Accept an invitation to become a guardian.
    
    Args:
        db: Database session.
        guardian_id: ID of the user accepting the invitation.
        code: Invitation code.
        
    Returns:
        The created Guardian relationship.
        
    Raises:
        ValueError: If code is invalid, expired, or self-invite.
    """
    # Check code validity
    data = _invitation_codes.get(code)
    if not data:
        raise ValueError("Invalid invitation code")
        
    if data["expires_at"] < datetime.utcnow():
        del _invitation_codes[code]
        raise ValueError("Invitation code expired")
        
    ward_id = data["user_id"]
    
    if ward_id == guardian_id:
        raise ValueError("Cannot be your own guardian")
        
    # Check if relationship already exists
    stmt = select(Guardian).where(
        and_(
            Guardian.ward_id == ward_id,
            Guardian.guardian_id == guardian_id
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise ValueError("Already a guardian for this user")
        
    # Create relationship
    guardian = Guardian(
        ward_id=ward_id,
        guardian_id=guardian_id,
        created_at=datetime.utcnow()
    )
    
    db.add(guardian)
    await db.commit()
    await db.refresh(guardian)
    
    # Invalidate code (one-time use)
    del _invitation_codes[code]
    
    logger.info(f"[GuardianService] User {guardian_id} became guardian for {ward_id}")
    return guardian


async def get_guardians(db: AsyncSession, user_id: UUID) -> list[User]:
    """Get list of guardians for a user.
    
    Returns User objects for display.
    """
    # Join Guardian -> User table to get guardian details
    stmt = (
        select(User)
        .join(Guardian, Guardian.guardian_id == User.id)
        .where(Guardian.ward_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_wards(db: AsyncSession, user_id: UUID) -> list[User]:
    """Get list of wards this user is protecting."""
    stmt = (
        select(User)
        .join(Guardian, Guardian.ward_id == User.id)
        .where(Guardian.guardian_id == user_id)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def remove_guardian(db: AsyncSession, ward_id: UUID, guardian_id: UUID) -> bool:
    """Remove a guardian relationship."""
    stmt = delete(Guardian).where(
        and_(
            Guardian.ward_id == ward_id,
            Guardian.guardian_id == guardian_id
        )
    )
    result = await db.execute(stmt)
    await db.commit()
    
    return result.rowcount > 0
