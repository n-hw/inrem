"""Add onboarding_completed_at to users

Revision ID: b5c6d7e8f9a0
Revises: f4b1c2a3d8e7
Create Date: 2026-05-21 00:00:00.000000

신규 사용자 온보딩 완료 시각을 기록. NULL = 온보딩 미완료.
재로그인 시 NULL 이 아니면 온보딩 건너뜀.

기존 사용자(NULL → NULL): 마이그레이션 후 기존 사용자는 NULL 이 되어
온보딩 화면을 보게 됨. v1.0 은 alpha 단계이므로 실 사용자 없음.
프로덕션 사용자 보유 시 배포 전 backfill 필요:
  UPDATE users SET onboarding_completed_at = NOW() WHERE onboarding_completed_at IS NULL;
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b5c6d7e8f9a0"
down_revision: Union[str, None] = "f4b1c2a3d8e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("onboarding_completed_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed_at")
