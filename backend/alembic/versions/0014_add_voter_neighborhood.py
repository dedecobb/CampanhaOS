"""adiciona neighborhood (bairro) em voters (mais precisao geocodificacao)

Revision ID: 0014_add_voter_neighborhood
Revises: 0013_add_voter_address_detail
Create Date: 2026-08-16

Bairro é um dos campos aceitos pela entrada estruturada v6 do Mapbox — em
áreas de cobertura mais fraca (comum no Brasil fora de grandes centros),
esse campo extra ajuda a geocodificação a não cair só no centro da
cidade/CEP.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014_add_voter_neighborhood"
down_revision: str | None = "0013_add_voter_address_detail"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("voters", sa.Column("neighborhood", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("voters", "neighborhood")
