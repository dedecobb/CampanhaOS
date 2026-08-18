"""
Injeção de dependência (composition root) do autocadastro público.
"""

from typing import Annotated
from uuid import UUID

from fastapi import Depends

from src.application.voters.public_self_register import PublicSelfRegisterVoterUseCase
from src.infrastructure.cache.redis_client import redis_client
from src.infrastructure.database.session import set_tenant_context
from src.infrastructure.rate_limiting.redis_rate_limiter import RedisRateLimiter
from src.presentation.api.admin_dependencies import AdminTenantRepositoryDep
from src.presentation.api.dependencies import DbSession
from src.presentation.api.leaderships_dependencies import LeadershipRepositoryDep
from src.presentation.api.voters_dependencies import GeocodingServiceDep, VoterRepositoryDep


def get_rate_limiter() -> RedisRateLimiter:
    return RedisRateLimiter(redis_client)


RateLimiterDep = Annotated[RedisRateLimiter, Depends(get_rate_limiter)]


def get_public_self_register_use_case(
    session: DbSession,
    tenant_repository: AdminTenantRepositoryDep,
    voter_repository: VoterRepositoryDep,
    leadership_repository: LeadershipRepositoryDep,
    geocoding_service: GeocodingServiceDep,
    rate_limiter: RateLimiterDep,
) -> PublicSelfRegisterVoterUseCase:
    async def set_tenant_context_callback(tenant_id: UUID) -> None:
        await set_tenant_context(session, tenant_id)

    return PublicSelfRegisterVoterUseCase(
        tenant_repository,
        voter_repository,
        leadership_repository,
        geocoding_service,
        rate_limiter,
        set_tenant_context_callback,
    )
