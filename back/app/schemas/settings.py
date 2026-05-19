"""Schemas for Settings API (MonitoringPolicy)."""

from datetime import time
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.monitoring_policy import SensitivityLevel


UpsellFeature = Literal["family_share", "report_export", "extended_storage"]


class UpsellClickRequest(BaseModel):
    """Premium 기능 페이월 카드 클릭 이벤트.

    결제 모듈 구현 전 단계의 **전환 가설 검증**용 — DB 저장 없이 logger 만 남긴다.
    """

    feature: UpsellFeature = Field(
        description="어떤 유료 기능 카드를 탭했는지 (예: 'family_share')."
    )
    surface: str | None = Field(
        default=None,
        max_length=40,
        description="UI 노출 위치 (예: 'home', 'settings'). 분석용.",
    )


class UpsellClickResponse(BaseModel):
    success: bool
    feature: UpsellFeature


class MonitoringPolicyResponse(BaseModel):
    """Response schema for MonitoringPolicy."""
    threshold_hours: int = 12
    quiet_start: time = time(23, 0)
    quiet_end: time = time(7, 0)
    escalation_enabled: bool = True
    escalation_delay_minutes: int = 60
    sensitivity: SensitivityLevel = SensitivityLevel.NORMAL
    is_active: bool = True
    sms_fallback_enabled: bool = False

    @field_validator('escalation_enabled', 'is_active', 'sms_fallback_enabled', mode='before')
    @classmethod
    def default_bool(cls, v):
        return v if v is not None else False
    
    @field_validator('sensitivity', mode='before')
    @classmethod
    def default_sensitivity(cls, v):
        return v if v is not None else SensitivityLevel.NORMAL

    class Config:
        from_attributes = True


class MonitoringPolicyUpdate(BaseModel):
    """Request schema for updating MonitoringPolicy."""
    threshold_hours: int | None = Field(None, ge=1, le=168)  # 1h to 1 week
    quiet_start: time | None = None
    quiet_end: time | None = None
    escalation_enabled: bool | None = None
    escalation_delay_minutes: int | None = Field(None, ge=0, le=1440)  # 0 to 24h
    sensitivity: SensitivityLevel | None = None
    is_active: bool | None = None
    sms_fallback_enabled: bool | None = None
