"""
Router de autenticação.

Traduz HTTP <-> casos de uso. Nenhuma regra de negócio vive aqui — cada
endpoint só converte o schema Pydantic em DTO de aplicação, chama o caso
de uso, e converte o resultado de volta para um schema de resposta.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from src.application.auth.dto import LoginInput, RefreshTokenInput, RegisterTenantInput
from src.application.auth.login import LoginUseCase
from src.application.auth.refresh_token import RefreshTokenUseCase
from src.application.auth.register_tenant import RegisterTenantUseCase
from src.presentation.api.dependencies import CurrentUser, DbSession
from src.presentation.api.dependencies import get_login_use_case as _get_login_use_case
from src.presentation.api.dependencies import get_refresh_token_use_case as _get_refresh_token_use_case
from src.presentation.api.dependencies import get_register_tenant_use_case as _get_register_use_case
from src.presentation.api.v1.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterTenantRequest,
    RegisterTenantResponse,
    TokenResponse,
    UserMeResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=RegisterTenantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registra uma nova campanha (tenant) com seu usuário administrador",
)
async def register_tenant(
    request: RegisterTenantRequest,
    session: DbSession,
    use_case: Annotated[RegisterTenantUseCase, Depends(_get_register_use_case)],
) -> RegisterTenantResponse:
    output = await use_case.execute(
        RegisterTenantInput(
            tenant_name=request.tenant_name,
            admin_name=request.admin_name,
            admin_email=request.admin_email,
            admin_password=request.admin_password,
        )
    )
    # Commit no limite da requisição (presentation), não dentro do
    # repository/caso de uso — ver nota de decisão no documento fonte da
    # verdade (Módulo 1 / Bloco E).
    await session.commit()
    return RegisterTenantResponse(tenant_id=output.tenant_id, user_id=output.user_id)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Autentica um usuário dentro de um tenant e retorna access + refresh token",
)
async def login(
    request: LoginRequest,
    session: DbSession,
    use_case: Annotated[LoginUseCase, Depends(_get_login_use_case)],
) -> TokenResponse:
    output = await use_case.execute(
        LoginInput(tenant_id=request.tenant_id, email=request.email, password=request.password)
    )
    # Login não escreve dados novos, mas o `SET LOCAL` do contexto de
    # tenant só é válido dentro de uma transação — precisamos encerrar a
    # transação de leitura corretamente (commit de uma leitura é seguro,
    # não tem efeito colateral de dado).
    await session.commit()
    return TokenResponse(access_token=output.access_token, refresh_token=output.refresh_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renova o par de tokens a partir de um refresh token válido (rotação: o antigo é revogado)",
)
async def refresh_token(
    request: RefreshTokenRequest,
    session: DbSession,
    use_case: Annotated[RefreshTokenUseCase, Depends(_get_refresh_token_use_case)],
) -> TokenResponse:
    output = await use_case.execute(RefreshTokenInput(refresh_token=request.refresh_token))
    await session.commit()
    return TokenResponse(access_token=output.access_token, refresh_token=output.refresh_token)


@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Retorna os dados do usuário autenticado (endpoint protegido de exemplo)",
)
async def get_me(current_user: CurrentUser) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        tenant_id=current_user.tenant_id,
        name=current_user.name,
        email=str(current_user.email),
        role_names=current_user.role_names,
    )
