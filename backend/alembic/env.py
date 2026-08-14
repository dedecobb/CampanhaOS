"""
Configuração de execução das migrações Alembic.

Ponto importante: nosso projeto usa SQLAlchemy assíncrono (asyncpg), então
não podemos usar o template padrão (síncrono) que o `alembic init` gera.
Este arquivo usa o padrão oficial recomendado pela documentação do
SQLAlchemy para Alembic + engine assíncrona.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.config.settings import get_settings
from src.infrastructure.database.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Fonte única da verdade da URL de conexão: o Settings do projeto (que lê
# do .env). O Alembic usa especificamente a URL de MIGRAÇÃO (superuser) —
# nunca a URL de aplicação (`database_url`), que agora aponta para um
# usuário restrito sem privilégio para criar tabelas/policies/roles.
config.set_main_option("sqlalchemy.url", get_settings().migration_database_url)

# target_metadata é o que permite `alembic revision --autogenerate`
# detectar diferenças entre os models.py e o schema atual do banco.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera SQL sem se conectar ao banco (usado para revisar SQL antes de aplicar)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Conecta de verdade ao banco (async) e aplica as migrações."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
