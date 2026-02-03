"""PulseEvent model for Guardian Pulse.

Tracks the lifecycle of a welfare check event from trigger to resolution.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class PulseStage(str, Enum):
    """Current escalation stage of a pulse event."""
    SOFT_CHECK = "soft_check"       # Level 1: User notification sent
    GUARDIAN_ALERT = "guardian_alert"  # Level 2: Guardian notified
    EMERGENCY = "emergency"         # Level 3: Emergency escalation (future)


class PulseStatus(str, Enum):
    """Status of a pulse event."""
    OPEN = "open"           # Event is active, awaiting response
    RESOLVED = "resolved"    # User confirmed they're okay
    DISMISSED = "dismissed"  # Guardian marked as checked
    EXPIRED = "expired"      # No response received, event timed out


class PulseEvent(Base):
    """A single welfare check event lifecycle.
    
    Created when user exceeds inactivity threshold.
    Tracks progression through escalation stages until resolution.
    """
    __tablename__ = "pulse_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Event lifecycle
    status = Column(SQLEnum(PulseStatus), nullable=False, default=PulseStatus.OPEN)
    current_stage = Column(SQLEnum(PulseStage), nullable=False, default=PulseStage.SOFT_CHECK)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    soft_check_sent_at = Column(DateTime, nullable=True)
    guardian_notified_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Resolution details
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # User or Guardian who resolved
    resolution_method = Column(String, nullable=True)  # "user_response", "guardian_call", "auto_timeout"
    resolution_note = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="pulse_events")
    resolver = relationship("User", foreign_keys=[resolved_by])
