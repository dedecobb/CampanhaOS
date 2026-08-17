"""adiciona public_registration_token em tenants

Revision ID: 0017_add_tenant_reg_token
Revises: 0016_add_voter_gender_birth
Create Date: 2026-08-17

Token do link de autocadastro público — NULL por padrão (desativado),
gerado sob demanda pela própria campanha. `tenants` não tem RLS (é a raiz
do isolamento, ver Módulo 1), então esse campo não precisa de nenhuma
proteção extra a nível de banco.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_add_tenant_reg_token"
down_revision: str | None = "0016_add_voter_gender_birth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("public_registration_token", sa.String(64), nullable=True))
    op.create_index(
        "ix_tenants_public_registration_token", "tenants", ["public_registration_token"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_tenants_public_registration_token", table_name="tenants")
    op.drop_column("tenants", "public_registration_token")
