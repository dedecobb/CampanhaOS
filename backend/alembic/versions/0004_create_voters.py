"""cria tabela voters (eleitores) com RLS

Revision ID: 0004_create_voters
Revises: 0003_sync_app_role_password
Create Date: 2026-08-01

Primeira tabela de negócio do projeto (fora do módulo de Auth). Segue
exatamente o padrão de RLS validado no Módulo 1: ENABLE + FORCE ROW LEVEL
SECURITY + policy baseada em `app.current_tenant_id`.

Nota: como a migração 0002 já configurou `ALTER DEFAULT PRIVILEGES` para
o usuário de aplicação (`campanhaos_app`), esta tabela nova já nasce com
as permissões corretas de SELECT/INSERT/UPDATE/DELETE para ele — não é
necessário repetir o GRANT aqui.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_create_voters"
down_revision: str | None = "0003_sync_app_role_password"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "voters",
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
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("address", sa.String(500), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column(
            "tags", postgresql.ARRAY(sa.String()), nullable=False, server_default="{}"
        ),
        sa.Column(
            "custom_fields", postgresql.JSONB(), nullable=False, server_default="{}"
        ),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("legal_basis", sa.String(50), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_voters_tenant_id", "voters", ["tenant_id"])
    op.create_index("ix_voters_name", "voters", ["name"])
    op.create_index("ix_voters_phone", "voters", ["phone"])
    op.create_index("ix_voters_tags", "voters", ["tags"], postgresql_using="gin")

    # --- Row-Level Security (mesmo padrão do Módulo 1) ---
    op.execute("ALTER TABLE voters ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE voters FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_voters ON voters
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_voters ON voters")
    op.drop_index("ix_voters_tags", table_name="voters")
    op.drop_index("ix_voters_phone", table_name="voters")
    op.drop_index("ix_voters_name", table_name="voters")
    op.drop_index("ix_voters_tenant_id", table_name="voters")
    op.drop_table("voters")
