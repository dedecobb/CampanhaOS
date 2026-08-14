"""
Engine e sessão async do SQLAlchemy.

Este arquivo tem uma responsabilidade extra além do "boilerplate" comum de
qualquer projeto FastAPI: gerenciar o contexto de tenant que alimenta o
Row-Level Security (RLS) do PostgreSQL (ADR-002).

Fluxo: a cada requisição autenticada, a camada de presentation (Bloco E)
vai chamar `set_tenant_context(session, tenant_id)` logo após abrir a
sessão, ANTES de qualquer outra query. Isso seta uma variável de sessão
Postgres que as policies de RLS leem para decidir quais linhas mostrar.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.settings import get_settings

settings = get_settings()

# `pool_pre_ping=True`: antes de reusar uma conexão do pool, o SQLAlchemy
# testa se ela ainda está viva. Sem isso, conexões que o PostgreSQL fechou
# por timeout (comum em ambientes cloud) causariam erros aleatórios e
# difíceis de depurar em produção.
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo_sql,
    pool_pre_ping=True,
)

# `expire_on_commit=False`: por padrão, o SQLAlchemy invalida os atributos
# de um objeto depois do commit, forçando uma nova query se você acessar
# esse objeto de novo. Em APIs, isso costuma causar um erro sutil (tentar
# acessar o objeto depois da sessão fechar, já na hora de montar a
# resposta HTTP). Desligamos porque controlamos explicitamente quando
# recarregar dados.
AsyncSessionFactory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession]:
    """
    Dependency do FastAPI para injetar uma sessão de banco por requisição.

    Uso: `session: AsyncSession = Depends(get_db_session)` num router.
    A sessão é sempre fechada ao final da requisição, com sucesso ou erro.
    """
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_tenant_context(session: AsyncSession, tenant_id: UUID) -> None:
    """
    Seta a variável de sessão que alimenta as policies de RLS.

    IMPORTANTE: usamos a função `set_config('app.current_tenant_id', valor,
    is_local=true)`, NÃO o comando `SET LOCAL app.current_tenant_id = :x`.
    O PostgreSQL não aceita bind parameters dentro de comandos `SET`/`SET
    LOCAL` — é uma limitação do protocolo (comandos `SET` são tratados como
    "comando de utilidade", fora do mecanismo normal de prepared statement
    que aceita `$1`, `$2` etc.). `set_config()` é uma função SQL comum, que
    aceita parâmetro normalmente, e o terceiro argumento `true` (`is_local`)
    reproduz exatamente a semântica de `SET LOCAL`: o valor só vale para a
    transação atual, sendo descartado no commit/rollback.

    Esse escopo transacional continua sendo essencial pelo mesmo motivo já
    documentado: conexões vêm de um POOL reutilizado entre requisições
    diferentes, e sem o `is_local=true` o tenant_id de uma requisição
    poderia "vazar" para a próxima que reutilizar a mesma conexão física.
    """
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": str(tenant_id)},
    )


async def clear_tenant_context(session: AsyncSession) -> None:
    """
    Usado apenas pelo contexto de super-admin (painel administrativo da
    plataforma, Módulo 7), que precisa enxergar todos os tenants. Reseta a
    variável para que nenhuma policy de tenant normal se aplique — o
    super-admin usa um caminho de código/permissão totalmente separado, que
    detalharemos quando chegarmos nesse módulo.
    """
    await session.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))
