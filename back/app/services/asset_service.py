"""Service layer for Heritage Box (digital legacy inventory).

Handles encryption / decryption of sensitive payloads and enforces
ownership boundaries. Routers should call into this module only — never
touch the repository directly with raw user input.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import get_encryption_service
from app.models.asset import ActionOnDeath, Asset, AssetType
from app.repositories import asset_repository
from app.schemas.asset import (
    AssetCreate,
    AssetResponse,
    AssetSecretResponse,
    AssetSummaryResponse,
    AssetUpdate,
)


def _to_response(asset: Asset) -> AssetResponse:
    """Convert an Asset ORM object into its safe response shape."""
    return AssetResponse(
        id=asset.id,
        user_id=asset.user_id,
        name=asset.name,
        type=asset.type,
        identifier=asset.identifier,
        action_on_death=asset.action_on_death,
        designated_executor_id=asset.designated_executor_id,
        note=asset.note,
        has_secret=bool(asset.encrypted_payload),
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


async def list_assets(
    db: AsyncSession,
    *,
    user_id: UUID,
    type_filter: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AssetResponse]:
    rows = await asset_repository.list_by_user(
        db, user_id, type_filter=type_filter, limit=limit, offset=offset
    )
    return [_to_response(a) for a in rows]


async def get_asset(
    db: AsyncSession, *, user_id: UUID, asset_id: UUID
) -> AssetResponse:
    asset = await asset_repository.get_by_id(db, asset_id, user_id=user_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    return _to_response(asset)


async def reveal_secret(
    db: AsyncSession, *, user_id: UUID, asset_id: UUID
) -> AssetSecretResponse:
    asset = await asset_repository.get_by_id(db, asset_id, user_id=user_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    secret = None
    if asset.encrypted_payload:
        secret = get_encryption_service().decrypt(asset.encrypted_payload)
    return AssetSecretResponse(id=asset.id, secret=secret)


async def create_asset(
    db: AsyncSession, *, user_id: UUID, payload: AssetCreate
) -> AssetResponse:
    encrypted = None
    if payload.secret:
        encrypted = get_encryption_service().encrypt(payload.secret)

    asset = Asset(
        user_id=user_id,
        name=payload.name,
        type=payload.type,
        identifier=payload.identifier,
        action_on_death=payload.action_on_death,
        designated_executor_id=payload.designated_executor_id,
        note=payload.note,
        encrypted_payload=encrypted,
    )
    asset = await asset_repository.create(db, asset)
    return _to_response(asset)


async def update_asset(
    db: AsyncSession, *, user_id: UUID, asset_id: UUID, payload: AssetUpdate
) -> AssetResponse:
    asset = await asset_repository.get_by_id(db, asset_id, user_id=user_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )

    if payload.name is not None:
        asset.name = payload.name
    if payload.type is not None:
        asset.type = payload.type
    if payload.identifier is not None:
        asset.identifier = payload.identifier
    if payload.action_on_death is not None:
        asset.action_on_death = payload.action_on_death
    if payload.designated_executor_id is not None:
        asset.designated_executor_id = payload.designated_executor_id
    if payload.note is not None:
        asset.note = payload.note

    if payload.clear_secret:
        asset.encrypted_payload = None
    elif payload.secret is not None:
        asset.encrypted_payload = get_encryption_service().encrypt(payload.secret)

    asset = await asset_repository.update(db, asset)
    return _to_response(asset)


async def delete_asset(
    db: AsyncSession, *, user_id: UUID, asset_id: UUID
) -> None:
    asset = await asset_repository.get_by_id(db, asset_id, user_id=user_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found"
        )
    await asset_repository.delete(db, asset)


async def summary(db: AsyncSession, *, user_id: UUID) -> AssetSummaryResponse:
    total = await asset_repository.count_by_user(db, user_id)
    by_type = await asset_repository.count_grouped(db, user_id, Asset.type)
    by_action = await asset_repository.count_grouped(
        db, user_id, Asset.action_on_death
    )

    # Make sure every enum key shows up, even with 0
    by_type_full = {t.value: 0 for t in AssetType} | by_type
    by_action_full = {a.value: 0 for a in ActionOnDeath} | by_action

    return AssetSummaryResponse(
        total=total, by_type=by_type_full, by_action=by_action_full
    )
