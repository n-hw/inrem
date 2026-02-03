"""ActivitySignal model for Guardian Pulse.

Tracks user activity signals (app opens, touch events, etc.)
to determine "Last Active" status.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class SignalType(str, Enum):
    """Types of activity signals that can be recorded."""
    APP_OPEN = "app_open"
    APP_FOREGROUND = "app_foreground"
    TOUCH_EVENT = "touch_event"
    HEARTBEAT = "heartbeat"
    MANUAL_CHECKIN = "manual_checkin"


class ActivitySignal(Base):
    """Records user activity for inactivity detection.
    
    Each signal represents a "proof of life" from the user's device.
    The most recent signal determines the user's last_active_at.
    """
    __tablename__ = "activity_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    signal_type = Column(SQLEnum(SignalType), nullable=False, default=SignalType.HEARTBEAT)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # Optional metadata
    device_info = Column(String, nullable=True)  # e.g., "iPhone 14, iOS 17.2"
    
    # Relationships
    user = relationship("User", back_populates="activity_signals")
