from datetime import datetime
from enum import Enum
from sqlalchemy import Column, DateTime, ForeignKey, Enum as SQLEnum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base

class TimerState(str, Enum):
    ACTIVE = "active"
    GRACE = "grace"     # In grace period
    EXPIRED = "expired" # Grace period passed, alert triggered
    STOPPED = "stopped" # User manually stopped or paused

class TimerStatus(Base):
    """Tracks the current state of a user's dead man's timer."""
    __tablename__ = "timer_statuses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    last_check_in = Column(DateTime, nullable=True)
    deadline_timestamp = Column(DateTime, nullable=True) # When the NEXT check-in is due (start of grace period)
    
    # Explicit status field
    status = Column(SQLEnum(TimerState), default=TimerState.STOPPED, nullable=False)
    
    user = relationship("User", back_populates="timer_status")
