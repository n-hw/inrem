"""MonitoringPolicy model for Guardian Pulse.

Stores user-configurable settings for inactivity monitoring.
"""

from datetime import time
from enum import Enum

from sqlalchemy import Column, Integer, Time, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.db.base import Base


class SensitivityLevel(str, Enum):
    """How aggressive the monitoring should be."""
    RELAXED = "relaxed"     # Longer thresholds, fewer notifications
    NORMAL = "normal"       # Balanced
    STRICT = "strict"       # Shorter thresholds, more proactive


class MonitoringPolicy(Base):
    """User's monitoring preferences and thresholds.
    
    Controls when and how the system should check on the user
    and when to escalate to guardians.
    """
    __tablename__ = "monitoring_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # Inactivity thresholds (in hours)
    threshold_hours = Column(Integer, nullable=False, default=12)  # Default: 12 hours
    
    # Quiet hours (no monitoring during sleep)
    quiet_start = Column(Time, nullable=False, default=time(23, 0))  # 11 PM
    quiet_end = Column(Time, nullable=False, default=time(7, 0))    # 7 AM
    
    # Escalation settings
    escalation_enabled = Column(Boolean, default=True)
    escalation_delay_minutes = Column(Integer, default=60)  # Wait 1 hour before notifying guardian
    
    # Sensitivity
    sensitivity = Column(SQLEnum(SensitivityLevel), default=SensitivityLevel.NORMAL)
    
    # Feature toggles
    is_active = Column(Boolean, default=True)  # Master on/off switch
    sms_fallback_enabled = Column(Boolean, default=False)  # Use SMS if push fails
    
    # Relationships
    user = relationship("User", back_populates="monitoring_policy")
