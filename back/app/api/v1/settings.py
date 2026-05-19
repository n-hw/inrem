"""Settings API endpoints for MonitoringPolicy."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.monitoring_policy import MonitoringPolicy
from app.schemas.settings import (
    MonitoringPolicyResponse,
    MonitoringPolicyUpdate,
    UpsellClickRequest,
    UpsellClickResponse,
)

logger = logging.getLogger("inrem.upsell")

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/policy", response_model=MonitoringPolicyResponse)
async def get_policy(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's monitoring policy settings."""
    result = await db.execute(
        select(MonitoringPolicy).where(MonitoringPolicy.user_id == current_user.id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        # Create default policy if not exists
        policy = MonitoringPolicy(user_id=current_user.id)
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    
    return policy


@router.patch("/policy", response_model=MonitoringPolicyResponse)
async def update_policy(
    update_data: MonitoringPolicyUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update current user's monitoring policy settings."""
    result = await db.execute(
        select(MonitoringPolicy).where(MonitoringPolicy.user_id == current_user.id)
    )
    policy = result.scalar_one_or_none()
    
    if not policy:
        # Create default policy if not exists
        policy = MonitoringPolicy(user_id=current_user.id)
        db.add(policy)
        await db.commit()
        await db.refresh(policy)
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(policy, field, value)

    await db.commit()
    await db.refresh(policy)

    return policy


@router.post("/upsell/click", response_model=UpsellClickResponse)
async def log_upsell_click(
    payload: UpsellClickRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Premium 페이월 카드 클릭을 로그로 남긴다.

    결제 모듈 구현 전 단계의 **전환 가설(KPI)** 검증용. DB 테이블 없이
    구조화 로그만 남기고, 추후 분석 파이프라인에서 집계한다.
    """
    logger.info(
        "upsell_click",
        extra={
            "user_id": str(current_user.id),
            "feature": payload.feature,
            "surface": payload.surface,
        },
    )
    return UpsellClickResponse(success=True, feature=payload.feature)
