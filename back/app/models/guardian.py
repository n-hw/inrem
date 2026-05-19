"""Guardian model for managing protective relationships."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Guardian(Base):
    """Represents a guardian-ward relationship.

    A user can be a guardian for many wards.
    A user (ward) can have many guardians.

    Database enforces uniqueness on ``(ward_id, guardian_id)`` so duplicate
    rows can't sneak in via raw SQL or future bugs. The service layer
    already rejects them — this is the belt to the suspenders.
    """
    __tablename__ = "guardians"
    __table_args__ = (
        UniqueConstraint("ward_id", "guardian_id", name="uq_guardians_ward_guardian"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    guardian_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    alias = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    ward = relationship("User", foreign_keys=[ward_id], back_populates="guardians")
    guardian = relationship("User", foreign_keys=[guardian_id], back_populates="wards")
