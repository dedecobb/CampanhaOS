"""converte colunas de timestamp para timestamptz (corrige bug de timezone)

Revision ID: 0005_use_timestamptz
Revises: 0004_create_voters
Create Date: 2026-08-01

Contexto (ver documento fonte da verdade, Módulo 2): o domínio sempre gera
datetimes timezone-aware (`datetime.now(UTC)`), mas as colunas de
timestamp foram criadas como `TIMESTAMP WITHOUT TIME ZONE`. Isso só
quebrou agora porque `Voter.soft_delete()` foi o primeiro caso a enviar um
datetime gerado em Python diretamente para uma coluna dessas — mas
`tenants`, `users` e `roles` tinham a mesma vulnerabilidade adormecida.
Convertendo tudo para `timestamptz` de uma vez, na causa raiz.

`postgresql_using`: obrigatório para converter `timestamp` -> `timestamptz`
com dados já existentes — instrui o Postgres a interpretar os valores
antigos (sem fuso) como já estando em UTC (verdade nesse projeto, já que
todo timestamp até agora veio de `now()` do servidor ou de `datetime.now
(UTC)`).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_use_timestamptz"
down_revision: str | None = "0004_create_voters"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TABLES_AND_COLUMNS = {
    "tenants": ["created_at", "updated_at"],
    "users": ["created_at", "updated_at"],
    "roles": ["created_at", "updated_at"],
    "voters": ["created_at", "updated_at", "deleted_at"],
}


def upgrade() -> None:
    for table, columns in _TABLES_AND_COLUMNS.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=True),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    for table, columns in _TABLES_AND_COLUMNS.items():
        for column in columns:
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=False),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )
