"""Settings API endpoints for MonitoringPolicy."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.monitoring_policy import MonitoringPolicy
from app.schemas.settings import MonitoringPolicyResponse, MonitoringPolicyUpdate

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
