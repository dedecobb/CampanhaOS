"""
Router PÚBLICO de autocadastro — sem CurrentUser de propósito, mesmo
espírito do webhook do WhatsApp (Módulo WhatsApp): a segurança aqui vem
do token na URL + limite de taxa, não de autenticação de usuário.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status

from src.application.tenant_settings.exceptions import InvalidRegistrationTokenError
from src.application.voters.public_self_register import PublicSelfRegisterVoterInput, PublicSelfRegisterVoterUseCase
from src.domain.tenants.repository import TenantRepository
from src.presentation.api.admin_dependencies import get_tenant_repository_for_admin
from src.presentation.api.dependencies import DbSession
from src.presentation.api.public_registration_dependencies import get_public_self_register_use_case
from src.presentation.api.v1.schemas.public_registration import (
    PublicCampaignInfoResponse,
    PublicVoterRegistrationRequest,
    PublicVoterRegistrationResponse,
)

router = APIRouter(prefix="/public/registration", tags=["public-registration"])


def _extract_client_ip(request: Request) -> str:
    """
    Por trás do proxy do Railway, `request.client.host` é o IP do PROXY,
    não do visitante real — o IP de verdade vem no header
    `X-Forwarded-For` (primeiro valor da lista, que pode ter vários IPs
    separados por vírgula se passar por múltiplos proxies em cadeia).
    Mesma lição aprendida no webhook do WhatsApp (verificação de
    assinatura precisou de `--forwarded-allow-ips`), aplicada aqui de
    propósito desde o início, sem precisar redescobrir o problema.
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.get("/{token}", response_model=PublicCampaignInfoResponse)
async def get_campaign_info(
    token: str,
    tenant_repository: Annotated[TenantRepository, Depends(get_tenant_repository_for_admin)],
) -> PublicCampaignInfoResponse:
    """Usado pela tela pública para mostrar 'Cadastro para [Nome da Campanha]' antes de exibir o formulário."""
    tenant = await tenant_repository.find_by_registration_token(token)
    if tenant is None:
        raise InvalidRegistrationTokenError
    return PublicCampaignInfoResponse(tenant_name=tenant.name)


@router.post("/{token}", response_model=PublicVoterRegistrationResponse, status_code=status.HTTP_201_CREATED)
async def self_register(
    token: str,
    request: Request,
    payload: PublicVoterRegistrationRequest,
    session: DbSession,
    use_case: Annotated[PublicSelfRegisterVoterUseCase, Depends(get_public_self_register_use_case)],
) -> PublicVoterRegistrationResponse:
    client_ip = _extract_client_ip(request)

    await use_case.execute(
        PublicSelfRegisterVoterInput(
            registration_token=token,
            client_ip=client_ip,
            name=payload.name,
            consent_given=payload.consent_given,
            phone=payload.phone,
            address=payload.address,
            city=payload.city,
            state=payload.state,
            postal_code=payload.postal_code,
            neighborhood=payload.neighborhood,
            gender=payload.gender,
            birth_date=payload.birth_date,
            leadership_id=payload.leadership_id,
        )
    )
    await session.commit()

    return PublicVoterRegistrationResponse(success=True, message="Cadastro realizado com sucesso!")
