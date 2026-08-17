"""
Injeção de dependência (composition root) dos casos de uso autenticados
de configuração de autocadastro (gerar/revogar/consultar o link).
"""

from typing import Annotated

from fastapi import Depends

from src.application.tenant_settings.generate_registration_token import GenerateRegistrationTokenUseCase
from src.application.tenant_settings.get_registration_token import GetRegistrationTokenUseCase
from src.application.tenant_settings.revoke_registration_token import RevokeRegistrationTokenUseCase
from src.presentation.api.admin_dependencies import AdminTenantRepositoryDep


def get_generate_registration_token_use_case(
    tenant_repository: AdminTenantRepositoryDep,
) -> GenerateRegistrationTokenUseCase:
    return GenerateRegistrationTokenUseCase(tenant_repository)


def get_revoke_registration_token_use_case(
    tenant_repository: AdminTenantRepositoryDep,
) -> RevokeRegistrationTokenUseCase:
    return RevokeRegistrationTokenUseCase(tenant_repository)


def get_get_registration_token_use_case(
    tenant_repository: AdminTenantRepositoryDep,
) -> GetRegistrationTokenUseCase:
    return GetRegistrationTokenUseCase(tenant_repository)
