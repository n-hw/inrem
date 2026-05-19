from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class UserConfig(Base):
    """User-specific configuration for the timer."""
    __tablename__ = "user_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Timer settings in seconds
    period = Column(Integer, default=86400, nullable=False)  # Default: 24 hours
    grace_period = Column(Integer, default=3600, nullable=False)  # Default: 1 hour
    
    # Feature toggle
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="config")
