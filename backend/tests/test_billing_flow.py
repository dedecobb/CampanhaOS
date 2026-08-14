"""
Testes de integração do módulo de billing (planos e assinaturas).
"""

import uuid
from datetime import date

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_platform_admin


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@campanhaos.dev"


async def _admin_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    email = _unique_email("admin-billing")
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


async def test_create_and_get_plan(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _admin_headers(client, db_session)

    create_response = await client.post(
        "/api/v1/admin/plans",
        headers=headers,
        json={"name": "Plano Básico", "price": "99.90", "max_users": 5},
    )
    assert create_response.status_code == 201, create_response.text
    plan = create_response.json()
    assert plan["name"] == "Plano Básico"
    assert plan["is_active"] is True

    get_response = await client.get(f"/api/v1/admin/plans/{plan['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == plan["id"]


async def test_create_plan_with_negative_price_returns_422(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _admin_headers(client, db_session)

    response = await client.post(
        "/api/v1/admin/plans", headers=headers, json={"name": "Plano Inválido", "price": "-10.00"}
    )
    assert response.status_code == 422


async def test_list_plans_only_active(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _admin_headers(client, db_session)

    active_response = await client.post(
        "/api/v1/admin/plans", headers=headers, json={"name": "Plano Ativo", "price": "50.00"}
    )
    active_plan_id = active_response.json()["id"]

    inactive_response = await client.post(
        "/api/v1/admin/plans", headers=headers, json={"name": "Plano Inativo", "price": "50.00"}
    )
    inactive_plan_id = inactive_response.json()["id"]
    await client.post(f"/api/v1/admin/plans/{inactive_plan_id}/deactivate", headers=headers)

    response = await client.get("/api/v1/admin/plans", headers=headers, params={"only_active": True})
    ids = {p["id"] for p in response.json()}
    assert active_plan_id in ids
    assert inactive_plan_id not in ids


async def test_update_plan_partial_preserves_unmentioned_limits(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    headers = await _admin_headers(client, db_session)

    create_response = await client.post(
        "/api/v1/admin/plans",
        headers=headers,
        json={"name": "Plano Update", "price": "100.00", "max_users": 10, "max_voters": 5000},
    )
    plan_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/admin/plans/{plan_id}", headers=headers, json={"price": "150.00"}
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["price"] == "150.00"
    assert updated["max_users"] == 10  # preservado
    assert updated["max_voters"] == 5000  # preservado


async def test_update_plan_can_set_limit_to_unlimited_explicitly(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    headers = await _admin_headers(client, db_session)

    create_response = await client.post(
        "/api/v1/admin/plans",
        headers=headers,
        json={"name": "Plano Ilimitável", "price": "200.00", "max_users": 10},
    )
    plan_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/admin/plans/{plan_id}", headers=headers, json={"max_users": None}
    )
    assert update_response.json()["max_users"] is None


async def test_assign_subscription_creates_and_then_updates(client: AsyncClient, db_session: AsyncSession) -> None:
    headers = await _admin_headers(client, db_session)
    tenant_id = await _register_tenant(client, tenant_name="Campanha Assinatura")

    plan_a_response = await client.post(
        "/api/v1/admin/plans", headers=headers, json={"name": "Plano A", "price": "99.00"}
    )
    plan_a_id = plan_a_response.json()["id"]

    assign_response = await client.put(
        f"/api/v1/admin/tenants/{tenant_id}/subscription",
        headers=headers,
        json={"plan_id": plan_a_id, "current_period_end": str(date(2026, 9, 1))},
    )
    assert assign_response.status_code == 200, assign_response.text
    subscription = assign_response.json()
    assert subscription["plan_id"] == plan_a_id
    assert subscription["status"] == "active"

    plan_b_response = await client.post(
        "/api/v1/admin/plans", headers=headers, json={"name": "Plano B", "price": "199.00"}
    )
    plan_b_id = plan_b_response.json()["id"]

    reassign_response = await client.put(
        f"/api/v1/admin/tenants/{tenant_id}/subscription",
        headers=headers,
        json={"plan_id": plan_b_id, "current_period_end": str(date(2026, 10, 1))},
    )
    reassigned = reassign_response.json()
    assert reassigned["plan_id"] == plan_b_id
    assert reassigned["id"] == subscription["id"]  # mesma assinatura, não duplicou

    get_response = await client.get(f"/api/v1/admin/tenants/{tenant_id}/subscription", headers=headers)
    assert get_response.json()["plan_id"] == plan_b_id


async def test_assign_subscription_with_inactive_plan_returns_409(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    headers = await _admin_headers(client, db_session)
    tenant_id = await _register_tenant(client, tenant_name="Campanha Plano Inativo")

    plan_response = await client.post(
        "/api/v1/admin/plans", headers=headers, json={"name": "Plano Descontinuado", "price": "50.00"}
    )
    plan_id = plan_response.json()["id"]
    await client.post(f"/api/v1/admin/plans/{plan_id}/deactivate", headers=headers)

    response = await client.put(
        f"/api/v1/admin/tenants/{tenant_id}/subscription",
        headers=headers,
        json={"plan_id": plan_id, "current_period_end": str(date(2026, 9, 1))},
    )
    assert response.status_code == 409


async def test_get_subscription_returns_null_when_tenant_has_none(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    headers = await _admin_headers(client, db_session)
    tenant_id = await _register_tenant(client, tenant_name="Campanha Sem Assinatura")

    response = await client.get(f"/api/v1/admin/tenants/{tenant_id}/subscription", headers=headers)
    assert response.status_code == 200
    assert response.json() is None
