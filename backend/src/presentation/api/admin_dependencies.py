"""
Injeção de dependência (composition root) do módulo de administração da
plataforma.

CRÍTICO: `get_current_platform_admin` é um mecanismo de autenticação
COMPLETAMENTE separado de `get_current_user` (dependencies.py, Módulo 1).
Nenhuma rota de super-admin usa `CurrentUser`, e nenhuma rota de tenant
usa `CurrentPlatformAdmin` — são dois "portões" que nunca se cruzam.
"""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.admin.activate_tenant import ActivateTenantUseCase
from src.application.admin.get_tenant import GetTenantUseCase
from src.application.admin.list_tenants import ListTenantsUseCase
from src.application.admin.login import AdminLoginUseCase
from src.application.admin.refresh_token import AdminRefreshTokenUseCase
from src.application.admin.suspend_tenant import SuspendTenantUseCase
from src.application.auth.exceptions import InvalidTokenError
from src.application.auth.ports import RefreshTokenBlocklist
from src.config.settings import Settings, get_settings
from src.domain.admin.entities import PlatformAdmin
from src.infrastructure.cache.redis_client import redis_client
from src.infrastructure.database.repositories.platform_admin_repository import SqlAlchemyPlatformAdminRepository
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.security.password_hasher import BcryptPasswordHasher
from src.infrastructure.security.platform_admin_jwt_handler import JwtPlatformAdminTokenService
from src.infrastructure.security.refresh_token_blocklist import RedisRefreshTokenBlocklist
from src.presentation.api.dependencies import DbSession

_bearer_scheme = HTTPBearer(auto_error=False)


def get_platform_admin_repository(session: DbSession) -> SqlAlchemyPlatformAdminRepository:
    return SqlAlchemyPlatformAdminRepository(session)


def get_admin_token_service(settings: Annotated[Settings, Depends(get_settings)]) -> JwtPlatformAdminTokenService:
    return JwtPlatformAdminTokenService(settings)


def get_admin_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


def get_admin_refresh_token_blocklist() -> RedisRefreshTokenBlocklist:
    return RedisRefreshTokenBlocklist(redis_client)


def get_tenant_repository_for_admin(session: DbSession) -> SqlAlchemyTenantRepository:
    return SqlAlchemyTenantRepository(session)


AdminRepositoryDep = Annotated[SqlAlchemyPlatformAdminRepository, Depends(get_platform_admin_repository)]
AdminTokenServiceDep = Annotated[JwtPlatformAdminTokenService, Depends(get_admin_token_service)]
AdminTenantRepositoryDep = Annotated[SqlAlchemyTenantRepository, Depends(get_tenant_repository_for_admin)]


def get_admin_login_use_case(
    admin_repository: AdminRepositoryDep,
    password_hasher: Annotated[BcryptPasswordHasher, Depends(get_admin_password_hasher)],
    token_service: AdminTokenServiceDep,
) -> AdminLoginUseCase:
    return AdminLoginUseCase(admin_repository, password_hasher, token_service)


def get_admin_refresh_token_use_case(
    admin_repository: AdminRepositoryDep,
    token_service: AdminTokenServiceDep,
    blocklist: Annotated[RefreshTokenBlocklist, Depends(get_admin_refresh_token_blocklist)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AdminRefreshTokenUseCase:
    ttl_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
    return AdminRefreshTokenUseCase(admin_repository, token_service, blocklist, ttl_seconds)


def get_list_tenants_use_case(tenant_repository: AdminTenantRepositoryDep) -> ListTenantsUseCase:
    return ListTenantsUseCase(tenant_repository)


def get_get_tenant_use_case(tenant_repository: AdminTenantRepositoryDep) -> GetTenantUseCase:
    return GetTenantUseCase(tenant_repository)


def get_suspend_tenant_use_case(tenant_repository: AdminTenantRepositoryDep) -> SuspendTenantUseCase:
    return SuspendTenantUseCase(tenant_repository)


def get_activate_tenant_use_case(tenant_repository: AdminTenantRepositoryDep) -> ActivateTenantUseCase:
    return ActivateTenantUseCase(tenant_repository)


async def get_current_platform_admin(
    session: DbSession,
    token_service: AdminTokenServiceDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> PlatformAdmin:
    """
    Equivalente a `get_current_user` (Módulo 1), mas para super-admin.
    Não precisa declarar contexto de tenant (RLS) — `platform_admins` não
    tem `tenant_id`, então não é afetada por RLS de forma nenhuma.
    """
    if credentials is None:
        raise InvalidTokenError("Nenhum token de autenticação foi fornecido")

    payload = token_service.decode_access_token(credentials.credentials)

    admin_repository = SqlAlchemyPlatformAdminRepository(session)
    admin = await admin_repository.find_by_id(payload.admin_id)
    if admin is None or not admin.is_active:
        raise InvalidTokenError("Administrador não encontrado ou inativo")

    return admin


CurrentPlatformAdmin = Annotated[PlatformAdmin, Depends(get_current_platform_admin)]
