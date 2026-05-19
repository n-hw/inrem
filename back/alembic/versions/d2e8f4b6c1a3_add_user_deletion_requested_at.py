"""Add deletion_requested_at to users (PIPA / 잊혀질 권리)

Revision ID: d2e8f4b6c1a3
Revises: c1a2b3d4e5f6
Create Date: 2026-05-19 18:00:00.000000

Adds a nullable timestamp column to the ``users`` table used to mark
accounts as "deletion requested." A background purger sweeps these
after the 30-day grace period defined in PRD §6.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d2e8f4b6c1a3"
down_revision: Union[str, None] = "c1a2b3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("deletion_requested_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "deletion_requested_at")
