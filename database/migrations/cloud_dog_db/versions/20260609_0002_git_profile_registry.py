"""git-mcp-server git_profile_registry (W28C-1705 GM2 / 1603-unblocker)

Durable repository-profile registry so admin-created profiles survive container
restart and are visible across the separate api / mcp / a2a surfaces. Mirrors
file-mcp's file_storage_profiles (full ProfileConfig JSON per row, soft-delete).

Revision ID: 20260609_0002
Revises: 20260305_0001
Create Date: 2026-06-09 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260609_0002"
down_revision = "20260305_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "git_profile_registry",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("display_name", sa.String(length=256), nullable=False, server_default=""),
        sa.Column("config_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_git_profile_registry_name"), "git_profile_registry", ["name"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_git_profile_registry_name"), table_name="git_profile_registry")
    op.drop_table("git_profile_registry")
