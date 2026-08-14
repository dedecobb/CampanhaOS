"""cria usuário de aplicação sem privilégio de superuser (corrige bypass de RLS)

Revision ID: 0002_create_app_role
Revises: 0001_initial_schema
Create Date: 2026-08-01

Contexto (ver documento fonte da verdade, Módulo 1 / Bloco F): o usuário
usado para RODAR esta migração (definido em POSTGRES_USER) é criado como
SUPERUSER pela imagem oficial do PostgreSQL. Superusuários SEMPRE ignoram
Row-Level Security, mesmo com FORCE ROW LEVEL SECURITY — isso não é
contornável via policy, é uma regra do próprio PostgreSQL.

Esta migração cria um segundo usuário, sem privilégio de superuser, que a
aplicação passa a usar em runtime (settings.database_url). O usuário
original (superuser) continua existindo só para rodar migrações futuras
(settings.migration_database_url).
"""
import os
from collections.abc import Sequence

from alembic import op

revision: str = "0002_create_app_role"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_APP_ROLE_NAME = "campanhaos_app"


def upgrade() -> None:
    # Senha lida de variável de ambiente (definida pelo operador, nunca
    # hardcoded no código versionado) — precisa bater com o que está em
    # DATABASE_URL (settings.py), já que é a mesma credencial.
    app_password = os.environ.get("APP_DB_PASSWORD")
    if not app_password:
        raise RuntimeError(
            "APP_DB_PASSWORD não definida no ambiente — necessária para criar "
            "o usuário de aplicação do PostgreSQL nesta migração."
        )

    # `DO $$ ... $$`: cria a role só se ainda não existir — torna a
    # migração idempotente (pode rodar de novo sem erro se já existir).
    # A senha é interpolada diretamente porque `CREATE ROLE` é DDL e não
    # aceita bind parameters (mesma limitação de `SET` que já vimos em
    # session.py) — aceitável aqui porque o valor vem de uma variável de
    # ambiente controlada pelo operador, não de entrada de usuário.
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{_APP_ROLE_NAME}') THEN
                CREATE ROLE {_APP_ROLE_NAME} WITH LOGIN PASSWORD '{app_password}' NOSUPERUSER;
            END IF;
        END
        $$;
        """
    )

    # Privilégio mínimo necessário: ler/escrever dados, nunca alterar
    # schema (CREATE TABLE, ALTER TABLE, DROP, criar policy — tudo isso
    # continua exclusivo do usuário de migração).
    op.execute(f"GRANT USAGE ON SCHEMA public TO {_APP_ROLE_NAME}")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {_APP_ROLE_NAME}")
    # Garante que tabelas criadas por migrações FUTURAS também concedam
    # esse mesmo privilégio automaticamente, sem precisar lembrar de um
    # GRANT manual em toda migração nova.
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {_APP_ROLE_NAME}"
    )


def downgrade() -> None:
    op.execute(f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM {_APP_ROLE_NAME}")
    op.execute(f"REVOKE USAGE ON SCHEMA public FROM {_APP_ROLE_NAME}")
    op.execute(f"DROP ROLE IF EXISTS {_APP_ROLE_NAME}")
