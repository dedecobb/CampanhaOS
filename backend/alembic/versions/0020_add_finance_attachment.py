"""adiciona campos de anexo em finance_transactions

Revision ID: 0020_add_finance_attachment
Revises: 0019_add_tenant_voter_goal
Create Date: 2026-08-17

Um anexo por lançamento — arquivo em si mora no Cloudflare R2, aqui só
guardamos a referência (chave/caminho) e metadados de exibição.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020_add_finance_attachment"
down_revision: str | None = "0019_add_tenant_voter_goal"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("finance_transactions", sa.Column("attachment_storage_key", sa.String(500), nullable=True))
    op.add_column("finance_transactions", sa.Column("attachment_filename", sa.String(255), nullable=True))
    op.add_column("finance_transactions", sa.Column("attachment_content_type", sa.String(100), nullable=True))
    op.add_column("finance_transactions", sa.Column("attachment_size_bytes", sa.BigInteger(), nullable=True))


def downgrade() -> None:
    op.drop_column("finance_transactions", "attachment_size_bytes")
    op.drop_column("finance_transactions", "attachment_content_type")
    op.drop_column("finance_transactions", "attachment_filename")
    op.drop_column("finance_transactions", "attachment_storage_key")
