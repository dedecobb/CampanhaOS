"""
Testes de integração da autenticação de super-admin (nível de API).
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_platform_admin


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@campanhaos.dev"


async def test_admin_login_success(client: AsyncClient, db_session: AsyncSession) -> None:
    email = _unique_email("admin-login")
    await create_test_platform_admin(db_session, email=email, password="senha_admin_123")

    response = await client.post("/api/v1/admin/auth/login", json={"email": email, "password": "senha_admin_123"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_admin_login_with_wrong_password_fails(client: AsyncClient, db_session: AsyncSession) -> None:
    email = _unique_email("admin-wrong-pw")
    await create_test_platform_admin(db_session, email=email, password="senha_admin_123")

    response = await client.post("/api/v1/admin/auth/login", json={"email": email, "password": "senha_errada"})
    assert response.status_code == 401


async def test_admin_endpoints_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/admin/tenants")
    assert response.status_code == 401


async def test_admin_refresh_token_rotation(client: AsyncClient, db_session: AsyncSession) -> None:
    email = _unique_email("admin-refresh")
    await create_test_platform_admin(db_session, email=email, password="senha_admin_123")

    login_response = await client.post(
        "/api/v1/admin/auth/login", json={"email": email, "password": "senha_admin_123"}
    )
    original_refresh_token = login_response.json()["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/admin/auth/refresh", json={"refresh_token": original_refresh_token}
    )
    assert refresh_response.status_code == 200, refresh_response.text
    new_refresh_token = refresh_response.json()["refresh_token"]
    assert new_refresh_token != original_refresh_token

    # Reuso do token antigo (rotação) deve ser rejeitado — mesma regra do
    # refresh de usuário normal (Módulo 1).
    reuse_response = await client.post(
        "/api/v1/admin/auth/refresh", json={"refresh_token": original_refresh_token}
    )
    assert reuse_response.status_code == 401
