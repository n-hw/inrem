"""Expand assets table for Heritage Box

Revision ID: c1a2b3d4e5f6
Revises: 7fafa3ba0a2c
Create Date: 2026-05-19 00:00:00.000000

Adds Heritage Box columns to the existing ``assets`` table:
- ``name``               (display name)
- ``identifier``         (account email / handle, plaintext)
- ``action_on_death``    (delete | memorialize | transfer | keep_private)
- ``designated_executor_id`` (FK -> users.id, nullable)
- ``note``               (freeform memo)
- ``created_at`` / ``updated_at`` (timestamps)

Also relaxes the legacy columns:
- ``encrypted_payload``: LargeBinary NOT NULL -> Text NULL (Fernet returns base64 str)
- ``iv``: dropped (Fernet manages its own IV)
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "7fafa3ba0a2c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) New columns (nullable=True first so existing rows survive,
    #    then backfill + tighten nullability for the required ones)
    op.add_column("assets", sa.Column("name", sa.String(length=120), nullable=True))
    op.add_column("assets", sa.Column("identifier", sa.String(length=255), nullable=True))
    op.add_column(
        "assets",
        sa.Column("action_on_death", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "assets",
        sa.Column("designated_executor_id", sa.UUID(), nullable=True),
    )
    op.add_column("assets", sa.Column("note", sa.Text(), nullable=True))
    op.add_column(
        "assets",
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )
    op.add_column(
        "assets",
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
    )

    # 2) Backfill defaults for required columns
    op.execute("UPDATE assets SET name = COALESCE(name, type, 'Untitled')")
    op.execute(
        "UPDATE assets SET action_on_death = COALESCE(action_on_death, 'keep_private')"
    )
    op.execute(
        "UPDATE assets SET created_at = COALESCE(created_at, CURRENT_TIMESTAMP)"
    )
    op.execute(
        "UPDATE assets SET updated_at = COALESCE(updated_at, CURRENT_TIMESTAMP)"
    )

    # 3) Tighten NOT NULL on required columns
    op.alter_column("assets", "name", nullable=False)
    op.alter_column("assets", "action_on_death", nullable=False)
    op.alter_column("assets", "created_at", nullable=False)
    op.alter_column("assets", "updated_at", nullable=False)

    # 4) FK for designated_executor_id
    op.create_foreign_key(
        "fk_assets_designated_executor_id_users",
        "assets",
        "users",
        ["designated_executor_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # 5) Index on user_id for faster per-user queries
    op.create_index(op.f("ix_assets_user_id"), "assets", ["user_id"], unique=False)

    # 6) Relax legacy columns
    # encrypted_payload: LargeBinary NOT NULL -> Text NULL
    op.alter_column(
        "assets",
        "encrypted_payload",
        existing_type=sa.LargeBinary(),
        type_=sa.Text(),
        existing_nullable=False,
        nullable=True,
        postgresql_using="encode(encrypted_payload, 'base64')",
    )
    # iv: drop
    op.drop_column("assets", "iv")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "assets",
        sa.Column("iv", sa.LargeBinary(), nullable=True),
    )
    op.alter_column(
        "assets",
        "encrypted_payload",
        existing_type=sa.Text(),
        type_=sa.LargeBinary(),
        existing_nullable=True,
        nullable=False,
        postgresql_using="decode(encrypted_payload, 'base64')",
    )

    op.drop_index(op.f("ix_assets_user_id"), table_name="assets")
    op.drop_constraint(
        "fk_assets_designated_executor_id_users", "assets", type_="foreignkey"
    )
    op.drop_column("assets", "updated_at")
    op.drop_column("assets", "created_at")
    op.drop_column("assets", "note")
    op.drop_column("assets", "designated_executor_id")
    op.drop_column("assets", "action_on_death")
    op.drop_column("assets", "identifier")
    op.drop_column("assets", "name")
