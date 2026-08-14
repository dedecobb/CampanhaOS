"""sincroniza a senha do usuário de aplicação (corrige descompasso da 0002)

Revision ID: 0003_sync_app_role_password
Revises: 0002_create_app_role
Create Date: 2026-08-01

Contexto (ver documento fonte da verdade): a migração 0002 só cria o
usuário `campanhaos_app` se ele ainda não existir — como o Alembic nunca
reexecuta uma migração já aplicada, se ela rodou antes do `.env` estar
configurado com o `APP_DB_PASSWORD` correto, o usuário ficou com uma
senha diferente da que está em DATABASE_URL, causando falha de
autenticação. Esta migração força a senha atual, resolvendo esse caso e
qualquer futuro descompasso semelhante.
"""
import os
from collections.abc import Sequence

from alembic import op

revision: str = "0003_sync_app_role_password"
down_revision: str | None = "0002_create_app_role"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_APP_ROLE_NAME = "campanhaos_app"


def upgrade() -> None:
    app_password = os.environ.get("APP_DB_PASSWORD")
    if not app_password:
        raise RuntimeError(
            "APP_DB_PASSWORD não definida no ambiente — necessária para sincronizar "
            "a senha do usuário de aplicação do PostgreSQL nesta migração."
        )

    op.execute(f"ALTER ROLE {_APP_ROLE_NAME} WITH PASSWORD '{app_password}'")


def downgrade() -> None:
    # Não há "senha anterior" rastreável para reverter — downgrade aqui é
    # um no-op intencional.
    pass
