from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.db.base import Base

class Record(Base):
    __tablename__ = "records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    media_url = Column(String, nullable=False)
    metadata_info = Column(JSONB)  # 'metadata' is reserved in SQLAlchemy
