"""ON DELETE SET NULL for cross-user FKs

Revision ID: f4b1c2a3d8e7
Revises: e3a9f1b2c4d5
Create Date: 2026-05-19 23:00:00.000000

Columns that reference *another* user (not the owner) must survive when
the referenced user is purged via PIPA 30-day flow.

- assets.designated_executor_id — 자산 자체는 owner 의 것이라 보존,
  지정인만 NULL 로.
- pulse_events.resolved_by — 이벤트 history 는 보존, resolver 만 NULL.

Owner-side FKs (e.g. assets.user_id) remain CASCADE via the ORM
relationship cascade configured on the User model.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "f4b1c2a3d8e7"
down_revision: Union[str, None] = "e3a9f1b2c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- assets.designated_executor_id ---
    # 기존 FK 이름은 `c1a2b3d4e5f6_expand_assets_for_heritage_box` 에서
    # 명시 지정한 `fk_assets_designated_executor_id_users`.
    op.drop_constraint(
        "fk_assets_designated_executor_id_users", "assets", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_assets_designated_executor_id_users",
        "assets",
        "users",
        ["designated_executor_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- pulse_events.resolved_by ---
    # Postgres 자동 이름 (`<table>_<col>_fkey`).
    op.drop_constraint(
        "pulse_events_resolved_by_fkey", "pulse_events", type_="foreignkey"
    )
    op.create_foreign_key(
        "pulse_events_resolved_by_fkey",
        "pulse_events",
        "users",
        ["resolved_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_assets_designated_executor_id_users", "assets", type_="foreignkey"
    )
    op.create_foreign_key(
        "fk_assets_designated_executor_id_users",
        "assets",
        "users",
        ["designated_executor_id"],
        ["id"],
    )
    op.drop_constraint(
        "pulse_events_resolved_by_fkey", "pulse_events", type_="foreignkey"
    )
    op.create_foreign_key(
        "pulse_events_resolved_by_fkey",
        "pulse_events",
        "users",
        ["resolved_by"],
        ["id"],
    )
