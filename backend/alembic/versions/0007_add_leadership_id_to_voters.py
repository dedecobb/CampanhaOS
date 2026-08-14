"""adiciona leadership_id em voters (associação eleitor-liderança)

Revision ID: 0007_add_leadership_id_to_voters
Revises: 0006_create_leaderships
Create Date: 2026-08-01

Precisa rodar DEPOIS de 0006 (a tabela leaderships precisa existir antes
de criarmos uma foreign key apontando para ela). `ondelete="SET NULL"`:
se uma liderança for removida, os eleitores associados a ela não são
apagados nem bloqueiam a exclusão — só perdem a associação.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_add_leadership_id_to_voters"
down_revision: str | None = "0006_create_leaderships"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "voters",
        sa.Column(
            "leadership_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leaderships.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_voters_leadership_id", "voters", ["leadership_id"])


def downgrade() -> None:
    op.drop_index("ix_voters_leadership_id", table_name="voters")
    op.drop_column("voters", "leadership_id")
