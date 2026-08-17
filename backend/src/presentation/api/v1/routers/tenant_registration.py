"""
Router autenticado de gerenciamento do link de autocadastro público.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.application.tenant_settings.dto import (
    GenerateRegistrationTokenInput,
    GetRegistrationTokenInput,
    RevokeRegistrationTokenInput,
)
from src.application.tenant_settings.generate_registration_token import GenerateRegistrationTokenUseCase
from src.application.tenant_settings.get_registration_token import GetRegistrationTokenUseCase
from src.application.tenant_settings.revoke_registration_token import RevokeRegistrationTokenUseCase
from src.config.settings import Settings, get_settings
from src.presentation.api.dependencies import CurrentUser, DbSession
from src.presentation.api.tenant_registration_dependencies import (
    get_generate_registration_token_use_case,
    get_get_registration_token_use_case,
    get_revoke_registration_token_use_case,
)
from src.presentation.api.v1.schemas.tenant_registration import RegistrationTokenResponse

router = APIRouter(prefix="/tenant/registration-link", tags=["tenant-registration"])


def _to_response(token: str | None, settings: Settings) -> RegistrationTokenResponse:
    if token is None:
        return RegistrationTokenResponse(token=None, registration_url=None)
    base_url = settings.frontend_url or ""
    return RegistrationTokenResponse(token=token, registration_url=f"{base_url}/cadastro/{token}")


@router.get("", response_model=RegistrationTokenResponse)
async def get_registration_link(
    current_user: CurrentUser,
    use_case: Annotated[GetRegistrationTokenUseCase, Depends(get_get_registration_token_use_case)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RegistrationTokenResponse:
    output = await use_case.execute(GetRegistrationTokenInput(tenant_id=current_user.tenant_id))
    return _to_response(output.token, settings)


@router.post("", response_model=RegistrationTokenResponse)
async def generate_registration_link(
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[GenerateRegistrationTokenUseCase, Depends(get_generate_registration_token_use_case)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RegistrationTokenResponse:
    """Gera (ou REGENERA, se já existir) o link — regenerar invalida o link antigo imediatamente."""
    output = await use_case.execute(GenerateRegistrationTokenInput(tenant_id=current_user.tenant_id))
    await session.commit()
    return _to_response(output.token, settings)


@router.delete("", status_code=204)
async def revoke_registration_link(
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[RevokeRegistrationTokenUseCase, Depends(get_revoke_registration_token_use_case)],
) -> None:
    await use_case.execute(RevokeRegistrationTokenInput(tenant_id=current_user.tenant_id))
    await session.commit()
