from sqlalchemy import Column, String, ForeignKey, LargeBinary
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db.base import Base

class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    encrypted_payload = Column(LargeBinary, nullable=False)
    iv = Column(LargeBinary, nullable=False)
