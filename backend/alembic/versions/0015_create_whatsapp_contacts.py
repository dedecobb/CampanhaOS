"""cria tabela whatsapp_contacts com RLS

Revision ID: 0015_create_whatsapp_contacts
Revises: 0014_add_voter_neighborhood
Create Date: 2026-08-16

UniqueConstraint(tenant_id, phone_number): mesmo telefone não pode ter
dois registros de opt-in no mesmo tenant — evita duplicata se o mesmo
número mandar mensagem mais de uma vez.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_create_whatsapp_contacts"
down_revision: str | None = "0014_add_voter_neighborhood"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phone_number", sa.String(20), nullable=False),
        sa.Column(
            "voter_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("voters.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("opted_in_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opt_in_source", sa.String(50), nullable=False),
        sa.Column("opted_out_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("tenant_id", "phone_number", name="uq_whatsapp_contacts_tenant_phone"),
    )

    op.create_index("ix_whatsapp_contacts_tenant_id", "whatsapp_contacts", ["tenant_id"])

    op.execute("ALTER TABLE whatsapp_contacts ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE whatsapp_contacts FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY tenant_isolation_whatsapp_contacts ON whatsapp_contacts
        USING (tenant_id::text = current_setting('app.current_tenant_id', true))
        WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation_whatsapp_contacts ON whatsapp_contacts")
    op.drop_index("ix_whatsapp_contacts_tenant_id", table_name="whatsapp_contacts")
    op.drop_table("whatsapp_contacts")
