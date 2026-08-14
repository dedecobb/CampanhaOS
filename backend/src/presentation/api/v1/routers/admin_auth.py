"""
Router de autenticação de super-admin.

Prefixo `/admin/auth`, separado de `/auth` (usuário normal). Não existe
endpoint de registro aqui, de propósito — o primeiro (e qualquer)
super-admin é criado via script de bootstrap (ver backend/scripts/
create_platform_admin.py), nunca por um endpoint público. Um endpoint de
"criar super-admin" acessível pela internet seria uma superfície de
ataque enorme para o app inteiro.
"""

from typing import Annotated

from fastapi import APIRouter, Depends

from src.application.admin.dto import AdminLoginInput, AdminRefreshTokenInput
from src.application.admin.login import AdminLoginUseCase
from src.application.admin.refresh_token import AdminRefreshTokenUseCase
from src.presentation.api.admin_dependencies import get_admin_login_use_case, get_admin_refresh_token_use_case
from src.presentation.api.dependencies import DbSession
from src.presentation.api.v1.schemas.admin_auth import (
    AdminLoginRequest,
    AdminRefreshTokenRequest,
    AdminTokenResponse,
)

router = APIRouter(prefix="/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminTokenResponse)
async def admin_login(
    request: AdminLoginRequest,
    session: DbSession,
    use_case: Annotated[AdminLoginUseCase, Depends(get_admin_login_use_case)],
) -> AdminTokenResponse:
    output = await use_case.execute(AdminLoginInput(email=request.email, password=request.password))
    await session.commit()
    return AdminTokenResponse(access_token=output.access_token, refresh_token=output.refresh_token)


@router.post("/refresh", response_model=AdminTokenResponse)
async def admin_refresh_token(
    request: AdminRefreshTokenRequest,
    session: DbSession,
    use_case: Annotated[AdminRefreshTokenUseCase, Depends(get_admin_refresh_token_use_case)],
) -> AdminTokenResponse:
    output = await use_case.execute(AdminRefreshTokenInput(refresh_token=request.refresh_token))
    await session.commit()
    return AdminTokenResponse(access_token=output.access_token, refresh_token=output.refresh_token)
