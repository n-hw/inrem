"""Heritage Box API — digital legacy inventory."""
from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limit import SECRET_REVEAL_LIMITER
from app.db.session import get_db
from app.models.user import User
from app.schemas.asset import (
    AssetCreate,
    AssetResponse,
    AssetSecretResponse,
    AssetSummaryResponse,
    AssetUpdate,
)
from app.services import asset_service

audit_logger = logging.getLogger("inrem.audit.heritage")

router = APIRouter(prefix="/heritage", tags=["heritage"])


@router.get("/assets", response_model=list[AssetResponse])
async def list_assets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    type_filter: str | None = Query(default=None, alias="type"),
    search: str | None = Query(
        default=None,
        max_length=120,
        description="이름 부분 일치 검색 (대소문자 무시).",
    ),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List the current user's Heritage Box assets, newest first."""
    return await asset_service.list_assets(
        db,
        user_id=current_user.id,
        type_filter=type_filter,
        search=search,
        limit=limit,
        offset=offset,
    )


@router.get("/assets/summary", response_model=AssetSummaryResponse)
async def get_summary(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Aggregated counts by type and post-mortem action."""
    return await asset_service.summary(db, user_id=current_user.id)


@router.post(
    "/assets", response_model=AssetResponse, status_code=status.HTTP_201_CREATED
)
async def create_asset(
    payload: AssetCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await asset_service.create_asset(
        db, user_id=current_user.id, payload=payload
    )


@router.get("/assets/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await asset_service.get_asset(
        db, user_id=current_user.id, asset_id=asset_id
    )


@router.get("/assets/{asset_id}/secret", response_model=AssetSecretResponse)
async def reveal_secret(
    asset_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return the decrypted sensitive payload.

    Hard guarantees:
    * **Rate-limited** per user (`SECRET_REVEAL_LIMITER`, 10/min) → 429 on burst.
    * **Audit-logged** to `inrem.audit.heritage` — every reveal leaves a trail.
    """
    SECRET_REVEAL_LIMITER.check(f"user:{current_user.id}")
    response = await asset_service.reveal_secret(
        db, user_id=current_user.id, asset_id=asset_id
    )
    audit_logger.info(
        "secret_reveal",
        extra={
            "user_id": str(current_user.id),
            "asset_id": str(asset_id),
            "had_secret": response.secret is not None,
        },
    )
    return response


@router.patch("/assets/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: UUID,
    payload: AssetUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await asset_service.update_asset(
        db, user_id=current_user.id, asset_id=asset_id, payload=payload
    )


@router.delete("/assets/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    await asset_service.delete_asset(
        db, user_id=current_user.id, asset_id=asset_id
    )
    return None
