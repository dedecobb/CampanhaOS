"""adiciona gender e birth_date em voters

Revision ID: 0016_add_voter_gender_birth
Revises: 0015_create_whatsapp_contacts
Create Date: 2026-08-16

Ambos opcionais — dado sensível de identidade de gênero nunca deve ser
exigido na criação do eleitor.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_add_voter_gender_birth"
down_revision: str | None = "0015_create_whatsapp_contacts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("voters", sa.Column("gender", sa.String(30), nullable=True))
    op.add_column("voters", sa.Column("birth_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("voters", "birth_date")
    op.drop_column("voters", "gender")
