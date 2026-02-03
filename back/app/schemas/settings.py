"""Schemas for Settings API (MonitoringPolicy)."""

from datetime import time
from pydantic import BaseModel, Field, field_validator

from app.models.monitoring_policy import SensitivityLevel


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
