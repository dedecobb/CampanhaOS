"""
Testes de integração da gestão de tenants (painel de super-admin).
"""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_platform_admin


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@campanhaos.dev"


async def _admin_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    email = _unique_email("admin-tenants")
    await create_test_platform_admin(db_session, email=email, password="senha_admin_123")
    login_response = await client.post(
        "/api/v1/admin/auth/login", json={"email": email, "password": "senha_admin_123"}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _register_tenant(client: AsyncClient, *, tenant_name: str) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": tenant_name,
            "admin_name": "Admin de Teste",
            "admin_email": _unique_email("tenant-owner"),
            "admin_password": "senha_forte_123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["tenant_id"]  # type: ignore[no-any-return]


async def test_list_tenants(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _admin_headers(client, db_session)
    unique_marker = uuid.uuid4().hex[:8]
    await _register_tenant(client, tenant_name=f"Campanha Listagem {unique_marker} A")
    await _register_tenant(client, tenant_name=f"Campanha Listagem {unique_marker} B")

    response = await client.get(
        "/api/v1/admin/tenants", headers=headers, params={"search": f"Listagem {unique_marker}"}
    )
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 2


async def test_get_tenant(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _admin_headers(client, db_session)
    tenant_id = await _register_tenant(client, tenant_name="Campanha Get Tenant")

    response = await client.get(f"/api/v1/admin/tenants/{tenant_id}", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "trial"


async def test_suspend_and_activate_tenant(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _admin_headers(client, db_session)
    tenant_id = await _register_tenant(client, tenant_name="Campanha Suspensão")

    suspend_response = await client.post(f"/api/v1/admin/tenants/{tenant_id}/suspend", headers=headers)
    assert suspend_response.status_code == 200, suspend_response.text
    assert suspend_response.json()["status"] == "suspended"

    activate_response = await client.post(f"/api/v1/admin/tenants/{tenant_id}/activate", headers=headers)
    assert activate_response.status_code == 200, activate_response.text
    assert activate_response.json()["status"] == "active"


async def test_get_nonexistent_tenant_returns_404(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _admin_headers(client, db_session)

    response = await client.get(f"/api/v1/admin/tenants/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404
