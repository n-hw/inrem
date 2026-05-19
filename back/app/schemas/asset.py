"""Pydantic schemas for Heritage Box assets."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.asset import ActionOnDeath, AssetType


class AssetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120, description="표시 이름")
    type: AssetType = AssetType.CUSTOM
    identifier: str | None = Field(
        default=None, max_length=255, description="계정 이메일/핸들 등 식별자 (평문)"
    )
    action_on_death: ActionOnDeath = ActionOnDeath.KEEP_PRIVATE
    designated_executor_id: UUID | None = None
    note: str | None = None


class AssetCreate(AssetBase):
    """Payload to create a new asset.

    `secret` is the user-supplied plaintext sensitive value (password, seed phrase…).
    It is encrypted server-side before persistence and never returned in responses.
    """

    secret: str | None = Field(
        default=None,
        description="암호화 저장될 민감 정보 (비밀번호, 시드 구문 등). 응답에 포함되지 않음.",
    )


class AssetUpdate(BaseModel):
    """Partial update — every field optional."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: AssetType | None = None
    identifier: str | None = Field(default=None, max_length=255)
    action_on_death: ActionOnDeath | None = None
    designated_executor_id: UUID | None = None
    note: str | None = None
    secret: str | None = Field(
        default=None,
        description="새 민감 정보를 보내면 기존 암호화 페이로드를 덮어씁니다.",
    )
    clear_secret: bool = Field(
        default=False,
        description="True 로 보내면 저장된 민감 정보를 삭제합니다 (secret 보다 우선).",
    )


class AssetResponse(AssetBase):
    """Standard asset response. Sensitive payload is never included."""

    id: UUID
    user_id: UUID
    has_secret: bool = Field(
        description="민감 정보 암호화 페이로드가 저장되어 있는지 여부",
    )
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssetSecretResponse(BaseModel):
    """Response when the user explicitly reveals the stored secret."""

    id: UUID
    secret: str | None


class AssetSummaryResponse(BaseModel):
    """Aggregated counts for the inventory dashboard."""

    total: int
    by_type: dict[str, int]
    by_action: dict[str, int]
