"""torna voters.created_by_user_id opcional (autocadastro público)

Revision ID: 0018_voter_creator_nullable
Revises: 0017_add_tenant_reg_token
Create Date: 2026-08-17

Um eleitor autocadastrado publicamente não tem um usuário da equipe que
o criou — created_by_user_id passa a aceitar NULL para representar
exatamente esse caso. FK continua ON DELETE RESTRICT para os valores
não-nulos (usuário criador continua protegido contra exclusão enquanto
tiver eleitor vinculado).
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0018_voter_creator_nullable"
down_revision: str | None = "0017_add_tenant_reg_token"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column("voters", "created_by_user_id", nullable=True)


def downgrade() -> None:
    # Nota: se houver linha com created_by_user_id NULL no momento do
    # downgrade, essa operação falha (esperado — não temos como inventar
    # um usuário criador que nunca existiu de verdade).
    op.alter_column("voters", "created_by_user_id", nullable=False)
