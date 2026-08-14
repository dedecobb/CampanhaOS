"""
Injeção de dependência (composition root) da camada de autenticação.

Este arquivo é o único lugar do sistema que conhece TANTO os casos de uso
(application) QUANTO as implementações concretas (infrastructure) —
propositalmente. É aqui que as portas definidas no domínio/aplicação são
"encaixadas" com suas implementações reais. Nenhum outro arquivo deveria
precisar importar `infrastructure.security.*` ou `infrastructure.database.
repositories.*` diretamente.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth.exceptions import InvalidTokenError
from src.application.auth.login import LoginUseCase
from src.application.auth.refresh_token import RefreshTokenUseCase
from src.application.auth.register_tenant import RegisterTenantUseCase
from src.config.settings import Settings, get_settings
from src.domain.users.entities import User
from src.infrastructure.cache.redis_client import redis_client
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.database.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.database.session import get_db_session
from src.infrastructure.database.tenant_context_setter import SqlAlchemyTenantContextSetter
from src.infrastructure.security.jwt_handler import JwtTokenService
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.infrastructure.security.refresh_token_blocklist import RedisRefreshTokenBlocklist

# `auto_error=False`: preferimos deixar nosso próprio InvalidTokenError
# levantar o erro (e ser tratado pelo handler global de ApplicationError,
# padronizando o formato de resposta) em vez do erro genérico que o
# HTTPBearer do FastAPI geraria sozinho para "header ausente".
_bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db_session)]


# --- Adapters "sem estado" (stateless) — podem ser criados livremente a
# cada requisição, sem custo relevante. ---


def get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


def get_token_service(settings: Annotated[Settings, Depends(get_settings)]) -> JwtTokenService:
    return JwtTokenService(settings)


def get_refresh_token_blocklist() -> RedisRefreshTokenBlocklist:
    return RedisRefreshTokenBlocklist(redis_client)


# --- Adapters ligados à sessão da requisição atual ---


def get_user_repository(session: DbSession) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(session)


def get_tenant_repository(session: DbSession) -> SqlAlchemyTenantRepository:
    return SqlAlchemyTenantRepository(session)


def get_tenant_context_setter(session: DbSession) -> SqlAlchemyTenantContextSetter:
    return SqlAlchemyTenantContextSetter(session)


# --- Casos de uso, já montados com as implementações reais ---


def get_register_tenant_use_case(
    tenant_repository: Annotated[SqlAlchemyTenantRepository, Depends(get_tenant_repository)],
    user_repository: Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
    tenant_context_setter: Annotated[SqlAlchemyTenantContextSetter, Depends(get_tenant_context_setter)],
) -> RegisterTenantUseCase:
    return RegisterTenantUseCase(tenant_repository, user_repository, password_hasher, tenant_context_setter)


def get_login_use_case(
    tenant_repository: Annotated[SqlAlchemyTenantRepository, Depends(get_tenant_repository)],
    user_repository: Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)],
    password_hasher: Annotated[BcryptPasswordHasher, Depends(get_password_hasher)],
    token_service: Annotated[JwtTokenService, Depends(get_token_service)],
    tenant_context_setter: Annotated[SqlAlchemyTenantContextSetter, Depends(get_tenant_context_setter)],
) -> LoginUseCase:
    return LoginUseCase(
        tenant_repository, user_repository, password_hasher, token_service, tenant_context_setter
    )


def get_refresh_token_use_case(
    user_repository: Annotated[SqlAlchemyUserRepository, Depends(get_user_repository)],
    token_service: Annotated[JwtTokenService, Depends(get_token_service)],
    refresh_token_blocklist: Annotated[RedisRefreshTokenBlocklist, Depends(get_refresh_token_blocklist)],
    tenant_context_setter: Annotated[SqlAlchemyTenantContextSetter, Depends(get_tenant_context_setter)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RefreshTokenUseCase:
    ttl_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
    return RefreshTokenUseCase(
        user_repository, token_service, refresh_token_blocklist, tenant_context_setter, ttl_seconds
    )


# --- Proteção de rotas autenticadas ---


async def get_current_user(
    session: DbSession,
    token_service: Annotated[JwtTokenService, Depends(get_token_service)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> User:
    """
    Dependency que qualquer rota protegida deve usar:
    `user: Annotated[User, Depends(get_current_user)]`.

    Decodifica o access token, declara o contexto de tenant na sessão
    (necessário por causa do RLS antes de qualquer query em `users`), e
    recarrega o usuário do banco — não confiamos apenas no payload do
    token para `is_active`, porque um usuário pode ter sido desativado
    DEPOIS que o token foi emitido, e o token continuaria "assinado
    corretamente" até expirar.
    """
    if credentials is None:
        raise InvalidTokenError("Nenhum token de autenticação foi fornecido")

    payload = token_service.decode_access_token(credentials.credentials)

    tenant_context_setter = SqlAlchemyTenantContextSetter(session)
    await tenant_context_setter.set_context(payload.tenant_id)

    user_repository = SqlAlchemyUserRepository(session)
    user = await user_repository.find_by_id(payload.tenant_id, payload.user_id)
    if user is None or not user.is_active:
        raise InvalidTokenError("Usuário não encontrado ou inativo")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
