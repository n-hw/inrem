"""Asset model for Heritage Box (digital legacy inventory).

Represents a digital asset the user wants to manage as part of their
end-of-life planning: social accounts, subscriptions, cloud storage,
crypto wallets, bank accounts, documents, etc.

Sensitive payload (passwords, seed phrases) is stored Fernet-encrypted
in `encrypted_payload`. Non-sensitive identifiers (account email,
service name) live in plaintext columns for search/UX.
"""
import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, ForeignKey, Text, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class AssetType(str, enum.Enum):
    """Asset category."""

    SOCIAL_ACCOUNT = "social_account"
    SUBSCRIPTION = "subscription"
    CLOUD_STORAGE = "cloud_storage"
    CRYPTO = "crypto"
    BANK_ACCOUNT = "bank_account"
    DOCUMENT = "document"
    CUSTOM = "custom"


class ActionOnDeath(str, enum.Enum):
    """What the user wants done with this asset after death."""

    DELETE = "delete"
    MEMORIALIZE = "memorialize"
    TRANSFER = "transfer"
    KEEP_PRIVATE = "keep_private"


class Asset(Base):
    __tablename__ = "assets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Display / classification
    name = Column(String(120), nullable=False)
    type = Column(
        Enum(AssetType, name="assettype", native_enum=False, length=32),
        nullable=False,
        default=AssetType.CUSTOM,
    )
    identifier = Column(String(255), nullable=True)  # e.g. account email, handle

    # Sensitive payload (Fernet-encrypted base64 string)
    encrypted_payload = Column(Text, nullable=True)

    # Post-mortem instructions
    action_on_death = Column(
        Enum(ActionOnDeath, name="actionondeath", native_enum=False, length=32),
        nullable=False,
        default=ActionOnDeath.KEEP_PRIVATE,
    )
    designated_executor_id = Column(
        UUID(as_uuid=True),
        # 다른 사용자가 삭제되어도 자산 자체는 보존하되 지정인만 NULL.
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Freeform memo
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
