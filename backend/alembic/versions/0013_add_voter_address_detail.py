"""adiciona city, state, postal_code em voters (precisão de geocodificação)

Revision ID: 0013_add_voter_address_detail
Revises: 0012_create_platform_admins
Create Date: 2026-08-16

Endereço sozinho é ambíguo para geocodificação (ex: "Rua das Flores, 123"
existe em centenas de cidades brasileiras) — estes campos, combinados,
permitem uma geocodificação muito mais precisa.

NOTA: o nome desta revisão precisou ser mais curto que o padrão usual —
a tabela `alembic_version` (interna do Alembic) tem a coluna
`version_num` limitada a 32 caracteres, e o nome mais descritivo original
("0013_add_address_detail_to_voters", 33 caracteres) estourava esse
limite, quebrando a migração com um erro só percebido rodando de
verdade. Ao nomear revisões futuras, manter isso em mente.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_add_voter_address_detail"
down_revision: str | None = "0012_create_platform_admins"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("voters", sa.Column("city", sa.String(255), nullable=True))
    op.add_column("voters", sa.Column("state", sa.String(2), nullable=True))
    op.add_column("voters", sa.Column("postal_code", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("voters", "postal_code")
    op.drop_column("voters", "state")
    op.drop_column("voters", "city")
