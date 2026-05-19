"""Unique constraint on (ward_id, guardian_id) for guardians

Revision ID: e3a9f1b2c4d5
Revises: d2e8f4b6c1a3
Create Date: 2026-05-19 22:00:00.000000

Database-level safety net so duplicate guardian↔ward rows cannot exist.
Service layer already rejects them in `guardian_service.accept_invitation`,
but defense in depth.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op


revision: str = "e3a9f1b2c4d5"
down_revision: Union[str, None] = "d2e8f4b6c1a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # If there are existing duplicates in prod, this will fail — operator
    # must dedupe first. The MVP has no production deployment yet so this
    # is safe.
    op.create_unique_constraint(
        "uq_guardians_ward_guardian",
        "guardians",
        ["ward_id", "guardian_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_guardians_ward_guardian",
        "guardians",
        type_="unique",
    )
