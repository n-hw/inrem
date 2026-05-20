from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from app.models.timer_status import TimerState

class TimerStatusResponse(BaseModel):
    user_id: UUID
    last_check_in: datetime | None
    deadline_timestamp: datetime | None
    status: TimerState

    model_config = ConfigDict(from_attributes=True)

class UserConfigResponse(BaseModel):
    period: int
    grace_period: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
