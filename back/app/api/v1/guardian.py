"""Guardian Management API endpoints."""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user
from app.core.rate_limit import GUARDIAN_INVITE_LIMITER
from app.models.user import User
from app.schemas.guardian import (
    CreateInvitationResponse,
    AcceptInvitationRequest,
    GuardianListResponse,
    WardListResponse,
    GuardianResponse,
)
from app.services import guardian_service

audit_logger = logging.getLogger("inrem.audit.guardian")

router = APIRouter(prefix="/guardian", tags=["guardian"])


@router.post("/invite", response_model=CreateInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create an invitation code for a guardian.

    Rate-limited to **5 invitations / hour per user** — invitation codes
    are stored in-memory so abuse would DoS the dict.
    """
    GUARDIAN_INVITE_LIMITER.check(f"guardian_invite:{current_user.id}")

    code = await guardian_service.create_invitation_code(current_user.id)
    # Expiration is hardcoded to 24h in service for now
    from datetime import datetime, timedelta
    expires_at = datetime.utcnow() + timedelta(days=1)

    audit_logger.info(
        "guardian_invitation_created",
        extra={
            "ward_id": str(current_user.id),
            "expires_at": expires_at.isoformat(),
        },
    )

    return CreateInvitationResponse(
        code=code,
        expires_at=expires_at
    )


@router.post("/accept", response_model=Any, status_code=status.HTTP_200_OK)
async def accept_invitation(
    request: AcceptInvitationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Accept an invitation to become a guardian.

    The potential guardian enters the code.
    """
    try:
        await guardian_service.accept_invitation(db, current_user.id, request.code)
        audit_logger.info(
            "guardian_invitation_accepted",
            extra={"guardian_id": str(current_user.id)},
        )
        return {"message": "You are now a guardian"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/list", response_model=GuardianListResponse)
async def list_guardians(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List my guardians (people watching over me)."""
    guardians = await guardian_service.get_guardians(db, current_user.id)
    return GuardianListResponse(guardians=guardians)


@router.get("/wards", response_model=WardListResponse)
async def list_wards(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List my wards (people I am watching)."""
    wards = await guardian_service.get_wards(db, current_user.id)
    return WardListResponse(wards=wards)


@router.delete("/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_guardian(
    guardian_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Remove a guardian. Audit-logged for compliance traceability."""
    from uuid import UUID
    try:
        gid = UUID(guardian_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    success = await guardian_service.remove_guardian(db, current_user.id, gid)
    if not success:
        raise HTTPException(status_code=404, detail="Guardian not found")
    audit_logger.info(
        "guardian_removed",
        extra={
            "ward_id": str(current_user.id),
            "guardian_id": str(gid),
        },
    )
