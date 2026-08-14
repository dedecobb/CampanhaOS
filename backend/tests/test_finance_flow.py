"""
Testes de integração do módulo Financeiro (nível de API).
"""

import uuid
from datetime import date

from httpx import AsyncClient


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@teste.campanhaos.dev"


async def _register_and_login(client: AsyncClient, *, tenant_name: str) -> tuple[str, dict[str, str]]:
    email = _unique_email("finance")
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": tenant_name,
            "admin_name": "Admin de Teste",
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
    token = login_response.json()["access_token"]

    return tenant_id, {"Authorization": f"Bearer {token}"}


async def test_create_and_get_transaction(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Finance - Create")

    create_response = await client.post(
        "/api/v1/finance",
        headers=headers,
        json={
            "type": "receita",
            "category": "Doação PF",
            "amount": "1000.00",
            "occurred_at": str(date.today()),
        },
    )
    assert create_response.status_code == 201, create_response.text
    transaction = create_response.json()
    assert transaction["category"] == "Doação PF"
    assert transaction["amount"] == "1000.00"

    get_response = await client.get(f"/api/v1/finance/{transaction['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == transaction["id"]


async def test_create_transaction_with_invalid_type_returns_422(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Finance - Tipo Inválido")

    response = await client.post(
        "/api/v1/finance",
        headers=headers,
        json={"type": "tipo_inventado", "category": "X", "amount": "100.00", "occurred_at": str(date.today())},
    )
    assert response.status_code == 422


async def test_create_transaction_with_negative_amount_returns_422(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Finance - Valor Negativo")

    response = await client.post(
        "/api/v1/finance",
        headers=headers,
        json={"type": "despesa", "category": "X", "amount": "-50.00", "occurred_at": str(date.today())},
    )
    assert response.status_code == 422


async def test_finance_endpoints_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/finance")
    assert response.status_code == 401


async def test_list_transactions_with_summary(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Finance - Resumo")

    async def create(type_: str, amount: str) -> None:
        response = await client.post(
            "/api/v1/finance",
            headers=headers,
            json={"type": type_, "category": "Categoria", "amount": amount, "occurred_at": str(date.today())},
        )
        assert response.status_code == 201, response.text

    await create("receita", "1000.00")
    await create("despesa", "300.50")
    await create("doacao", "500.00")

    list_response = await client.get("/api/v1/finance", headers=headers)
    assert list_response.status_code == 200, list_response.text
    body = list_response.json()
    assert body["total"] == 3
    summary = body["summary"]
    assert summary["total_receitas"] == "1000.00"
    assert summary["total_despesas"] == "300.50"
    assert summary["total_doacoes"] == "500.00"
    assert summary["saldo"] == "1199.50"


async def test_list_transactions_filtered_by_type_summary_respects_filter(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Finance - Resumo Filtrado")

    await client.post(
        "/api/v1/finance",
        headers=headers,
        json={"type": "receita", "category": "A", "amount": "700.00", "occurred_at": str(date.today())},
    )
    await client.post(
        "/api/v1/finance",
        headers=headers,
        json={"type": "despesa", "category": "B", "amount": "200.00", "occurred_at": str(date.today())},
    )

    filtered_response = await client.get("/api/v1/finance", headers=headers, params={"type": "despesa"})
    body = filtered_response.json()
    assert body["total"] == 1
    assert body["summary"]["total_receitas"] == "0"
    assert body["summary"]["total_despesas"] == "200.00"


async def test_update_transaction_partial(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Finance - Update")

    create_response = await client.post(
        "/api/v1/finance",
        headers=headers,
        json={
            "type": "despesa",
            "category": "Combustível",
            "amount": "150.00",
            "occurred_at": str(date.today()),
        },
    )
    transaction_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/finance/{transaction_id}", headers=headers, json={"amount": "180.00"}
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["amount"] == "180.00"
    assert updated["category"] == "Combustível"


async def test_delete_transaction_then_404(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Finance - Delete")

    create_response = await client.post(
        "/api/v1/finance",
        headers=headers,
        json={
            "type": "receita",
            "category": "A excluir",
            "amount": "100.00",
            "occurred_at": str(date.today()),
        },
    )
    transaction_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/finance/{transaction_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/finance/{transaction_id}", headers=headers)
    assert get_response.status_code == 404


async def test_cannot_access_transaction_from_another_tenant(client: AsyncClient) -> None:
    _, headers_a = await _register_and_login(client, tenant_name="Campanha Finance A - Isolamento")
    _, headers_b = await _register_and_login(client, tenant_name="Campanha Finance B - Isolamento")

    create_response = await client.post(
        "/api/v1/finance",
        headers=headers_a,
        json={
            "type": "receita",
            "category": "Do Tenant A",
            "amount": "100.00",
            "occurred_at": str(date.today()),
        },
    )
    transaction_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/finance/{transaction_id}", headers=headers_b)
    assert response.status_code == 404
