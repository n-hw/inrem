from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deceased = Column(Boolean, default=False)
    
    # Push notifications
    fcm_token = Column(String, nullable=True)  # Firebase Cloud Messaging token
    
    # Guardian Pulse: Last activity tracking
    last_active_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    
    # Relationships for Guardian Pulse
    activity_signals = relationship("ActivitySignal", back_populates="user", lazy="dynamic")
    monitoring_policy = relationship("MonitoringPolicy", back_populates="user", uselist=False)
    pulse_events = relationship("PulseEvent", foreign_keys="PulseEvent.user_id", back_populates="user", lazy="dynamic")
    
    # Guardian relationships
    guardians = relationship(
        "Guardian",
        foreign_keys="Guardian.ward_id",
        back_populates="ward",
        lazy="dynamic",
    )
    wards = relationship(
        "Guardian",
        foreign_keys="Guardian.guardian_id",
        back_populates="guardian",
        lazy="dynamic",
    )
