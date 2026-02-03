"""Guardian model for managing protective relationships."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Guardian(Base):
    """Represents a guardian-ward relationship.
    
    A user can be a guardian for many wards.
    A user (ward) can have many guardians.
    
    Attributes:
        ward_id: The ID of the user being protected.
        guardian_id: The ID of the user acting as guardian.
        alias: Optional nickname for the relationship (e.g., "Dad").
    """
    __tablename__ = "guardians"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ward_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    guardian_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    alias = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    ward = relationship("User", foreign_keys=[ward_id], back_populates="guardians")
    guardian = relationship("User", foreign_keys=[guardian_id], back_populates="wards")
