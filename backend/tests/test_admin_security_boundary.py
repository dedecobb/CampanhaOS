"""
Testes de fronteira de segurança entre autenticação de usuário normal e
de super-admin — o teste mais importante do Módulo 7.

Sem esses testes, um bug futuro (ex: alguém "simplificando" o JWT pra
usar o mesmo campo "type" nos dois sistemas) poderia passar despercebido
até um incidente de segurança real — um token de usuário vazado
permitindo acesso ao painel de TODAS as campanhas, ou um token de admin
sendo aceito como se fosse de um tenant qualquer.
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_platform_admin


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@campanhaos.dev"


async def _register_and_login_regular_user(client: AsyncClient) -> str:
    email = _unique_email("boundary-user")
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "Campanha Fronteira de Segurança",
            "admin_name": "Usuário de Teste",
            "admin_email": email,
            "admin_password": "senha_forte_123",
        },
    )
    assert register_response.status_code == 201, register_response.text
    tenant_id = register_response.json()["tenant_id"]

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_id": tenant_id, "email": email, "password": "senha_forte_123"},
    )
    assert login_response.status_code == 200, login_response.text
    return login_response.json()["access_token"]  # type: ignore[no-any-return]


async def _create_and_login_platform_admin(client: AsyncClient, db_session: AsyncSession) -> str:
    email = _unique_email("boundary-admin")
    await create_test_platform_admin(db_session, email=email, password="senha_admin_123")

    login_response = await client.post(
        "/api/v1/admin/auth/login", json={"email": email, "password": "senha_admin_123"}
    )
    assert login_response.status_code == 200, login_response.text
    return login_response.json()["access_token"]  # type: ignore[no-any-return]


async def test_regular_user_token_cannot_access_admin_endpoints(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """
    Um token de usuário de tenant válido, usado num endpoint de
    super-admin, deve ser rejeitado — mesmo sendo um token
    "criptograficamente válido" (assinado com a mesma chave secreta).
    """
    user_token = await _register_and_login_regular_user(client)

    response = await client.get(
        "/api/v1/admin/tenants", headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 401, (
        f"VULNERABILIDADE: token de usuário normal foi aceito num endpoint de admin! Status: {response.status_code}"
    )


async def test_admin_token_cannot_access_regular_tenant_endpoints(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """
    O inverso: um token de super-admin válido, usado num endpoint de
    tenant normal, também deve ser rejeitado.
    """
    admin_token = await _create_and_login_platform_admin(client, db_session)

    response = await client.get("/api/v1/voters", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 401, (
        f"VULNERABILIDADE: token de admin foi aceito num endpoint de tenant! Status: {response.status_code}"
    )


async def test_admin_refresh_token_cannot_be_used_as_regular_refresh_token(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """
    Mesma fronteira, mas para o REFRESH token — garante que nem o
    mecanismo de renovação permite cruzar os dois sistemas.
    """
    email = _unique_email("boundary-admin-refresh")
    await create_test_platform_admin(db_session, email=email, password="senha_admin_123")

    admin_login_response = await client.post(
        "/api/v1/admin/auth/login", json={"email": email, "password": "senha_admin_123"}
    )
    admin_refresh_token = admin_login_response.json()["refresh_token"]

    # Tenta usar o refresh token de ADMIN no endpoint de refresh de USUÁRIO normal.
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": admin_refresh_token})
    assert response.status_code == 401, (
        "VULNERABILIDADE: refresh token de admin foi aceito no endpoint de refresh de usuário normal!"
    )
