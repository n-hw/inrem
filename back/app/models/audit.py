from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor = Column(String, nullable=False)
    action = Column(String, nullable=False)
    target_id = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
