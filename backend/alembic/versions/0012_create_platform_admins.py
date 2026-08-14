"""cria tabela platform_admins (super-admins da plataforma, sem RLS)

Revision ID: 0012_create_platform_admins
Revises: 0011_create_subscriptions
Create Date: 2026-08-06

Tabela completamente separada de `users` — sem tenant_id, sem RLS, e-mail
único GLOBALMENTE (não por tenant).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_create_platform_admins"
down_revision: str | None = "0011_create_subscriptions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "platform_admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email", name="uq_platform_admins_email"),
    )


def downgrade() -> None:
    op.drop_table("platform_admins")
