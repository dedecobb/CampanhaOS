"""cria tabela leaderships (lideranças) com RLS

Revision ID: 0006_create_leaderships
Revises: 0005_use_timestamptz
Create Date: 2026-08-01

Mesmo padrão de RLS validado nos Módulos 1 e 2: ENABLE + FORCE ROW LEVEL
SECURITY + policy baseada em `app.current_tenant_id`. Graças ao `ALTER
DEFAULT PRIVILEGES` configurado na migração 0002, esta tabela já nasce
com as permissões corretas para o usuário de aplicação (`campanhaos_app`)
sem precisar de GRANT explícito aqui.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006_create_leaderships"
down_revision: str | None = "0005_use_timestamptz"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "leaderships",
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
        sa.Column("region", sa.String(255), nullable=True),
        sa.Column("estimated_votes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("influence_level", sa.String(10), nullable=False),
        sa.Column("team_size", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_leaderships_tenant_id", "leaderships", ["tenant_id"])
    op.create_index("ix_leaderships_name", "leaderships", ["name"])
    op.create_index("ix_leaderships_region", "leaderships", ["region"])

    op.execute("ALTER TABLE leaderships ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE leaderships FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_leaderships ON leaderships
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_leaderships ON leaderships")
    op.drop_index("ix_leaderships_region", table_name="leaderships")
    op.drop_index("ix_leaderships_name", table_name="leaderships")
    op.drop_index("ix_leaderships_tenant_id", table_name="leaderships")
    op.drop_table("leaderships")
