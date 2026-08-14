"""
Fixtures compartilhadas de teste.

IMPORTANTE: esta suíte de testes é de INTEGRAÇÃO — ela roda contra um
PostgreSQL e Redis reais (os mesmos serviços do docker-compose/CI), não
contra mocks. Antes de rodar `pytest`, as migrações precisam estar
aplicadas (`alembic upgrade head`) — não fazemos isso automaticamente
aqui de propósito, para que uma migração quebrada falhe de forma
explícita nesse passo, não escondida dentro de um erro de teste confuso.

Decisão de design: usamos uma engine SQLAlchemy separada da engine de
produção (`src/infrastructure/database/session.py`), configurada com
`NullPool` — cada checkout de conexão é uma conexão física NOVA, nunca
reaproveitada entre testes. Isso evita dois problemas ao mesmo tempo:
(1) conexões asyncpg presas ao event loop de um teste anterior, e
(2) qualquer estado residual (ex: contexto de tenant de um teste que
falhou no meio) vazando para o próximo teste através de uma conexão
reaproveitada "suja". A engine de produção continua com pool normal,
que é o comportamento certo para produção — isso é uma decisão só de
ambiente de teste.
"""

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.config.settings import get_settings
from src.domain.admin.entities import PlatformAdmin
from src.domain.users.value_objects import Email
from src.infrastructure.database.repositories.platform_admin_repository import SqlAlchemyPlatformAdminRepository
from src.infrastructure.database.session import get_db_session
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.presentation.api.main import app

_settings = get_settings()

_test_engine = create_async_engine(_settings.database_url, poolclass=NullPool)
_TestSessionFactory = async_sessionmaker(_test_engine, expire_on_commit=False, autoflush=False)


async def _override_get_db_session() -> AsyncGenerator[AsyncSession]:
    async with _TestSessionFactory() as session:
        try:
            yield session
        finally:
            await session.close()


# Faz a aplicação usar a engine de teste (NullPool) em vez da engine de
# produção sempre que rodada sob pytest — sem isso, o client de teste
# (fixture `client` abaixo) continuaria usando o pool de produção e os
# mesmos problemas de conexão reaproveitada voltariam a acontecer.
app.dependency_overrides[get_db_session] = _override_get_db_session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    """Cliente HTTP assíncrono que bate direto na aplicação real (sem subir servidor de verdade)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """
    Sessão de banco "crua", para os testes de baixo nível de RLS
    (test_tenant_isolation.py) que precisam executar SQL diretamente,
    fora do ciclo de vida normal de uma requisição HTTP. Usa a mesma
    engine de teste (NullPool) configurada acima.
    """
    async with _TestSessionFactory() as session:
        yield session
        await session.rollback()


async def create_test_platform_admin(
    session: AsyncSession,
    *,
    email: str,
    password: str = "senha_admin_123",
    name: str = "Admin de Teste",
) -> None:
    """
    Cria um PlatformAdmin direto via repository + commit. Necessário
    porque não existe (de propósito, ver Módulo 7) endpoint público de
    registro de super-admin — os testes precisam do mesmo acesso "de
    bootstrap" que o script `scripts/create_platform_admin.py` usa.
    """
    hasher = BcryptPasswordHasher()
    admin = PlatformAdmin.create(name=name, email=Email(email), password_hash=hasher.hash(password))
    await SqlAlchemyPlatformAdminRepository(session).save(admin)
    await session.commit()
