"""cria tabela finance_transactions (financeiro) com RLS

Revision ID: 0009_create_finance_transactions
Revises: 0008_create_events
Create Date: 2026-08-05

`amount` usa NUMERIC(12, 2), nunca FLOAT/DOUBLE PRECISION — dinheiro
exige precisão decimal exata, não aproximação binária de ponto flutuante.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_create_finance_transactions"
down_revision: str | None = "0008_create_events"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "finance_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("category", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("occurred_at", sa.Date(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        # CHECK constraint: reforça no banco a mesma regra que o domínio já
        # valida (amount > 0) — defesa em profundidade, mesmo princípio do
        # RLS: não confiar só na camada de aplicação para uma regra crítica.
        sa.CheckConstraint("amount > 0", name="ck_finance_transactions_amount_positive"),
    )

    op.create_index("ix_finance_transactions_tenant_id", "finance_transactions", ["tenant_id"])
    op.create_index("ix_finance_transactions_occurred_at", "finance_transactions", ["occurred_at"])
    op.create_index("ix_finance_transactions_type", "finance_transactions", ["type"])

    op.execute("ALTER TABLE finance_transactions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE finance_transactions FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_finance_transactions ON finance_transactions
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_finance_transactions ON finance_transactions")
    op.drop_index("ix_finance_transactions_type", table_name="finance_transactions")
    op.drop_index("ix_finance_transactions_occurred_at", table_name="finance_transactions")
    op.drop_index("ix_finance_transactions_tenant_id", table_name="finance_transactions")
    op.drop_table("finance_transactions")
