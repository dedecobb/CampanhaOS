"""cria tabela plans (catálogo de planos, global, sem RLS)

Revision ID: 0010_create_plans
Revises: 0009_create_finance_transactions
Create Date: 2026-08-06

Diferente de toda tabela de negócio até agora: SEM tenant_id, SEM RLS —
é um catálogo global (mesmo padrão de `permissions`, Módulo 1).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0010_create_plans"
down_revision: str | None = "0009_create_finance_transactions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_users", sa.Integer(), nullable=True),
        sa.Column("max_voters", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("price >= 0", name="ck_plans_price_non_negative"),
    )


def downgrade() -> None:
    op.drop_table("plans")
