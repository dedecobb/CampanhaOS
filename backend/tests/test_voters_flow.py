"""
Testes de integração do CRM de Eleitores (nível de API).
"""

import uuid

from httpx import AsyncClient


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@teste.campanhaos.dev"


async def _register_and_login(client: AsyncClient, *, tenant_name: str) -> tuple[str, dict[str, str]]:
    """Registra um novo tenant + admin, loga, e retorna (tenant_id, headers de autenticação)."""
    email = _unique_email("voters")
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


async def test_create_and_get_voter(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Voters - Create")

    create_response = await client.post(
        "/api/v1/voters",
        headers=headers,
        json={
            "name": "Maria da Silva",
            "legal_basis": "consentimento",
            "phone": "65999998888",
            "tags": ["lideranca", "zona-norte"],
        },
    )
    assert create_response.status_code == 201, create_response.text
    voter = create_response.json()
    assert voter["name"] == "Maria da Silva"
    assert voter["tags"] == ["lideranca", "zona-norte"]

    get_response = await client.get(f"/api/v1/voters/{voter['id']}", headers=headers)
    assert get_response.status_code == 200, get_response.text
    assert get_response.json()["id"] == voter["id"]


async def test_create_voter_with_invalid_legal_basis_returns_422(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Voters - Base Legal Inválida")

    response = await client.post(
        "/api/v1/voters",
        headers=headers,
        json={"name": "Eleitor Teste", "legal_basis": "base_legal_inventada"},
    )
    # Rejeitado já pelo Pydantic (Literal), antes de chegar no caso de uso.
    assert response.status_code == 422


async def test_voter_endpoints_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/voters")
    assert response.status_code == 401


async def test_list_and_filter_voters(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Voters - Listagem")

    await client.post(
        "/api/v1/voters",
        headers=headers,
        json={"name": "Ana Souza", "legal_basis": "consentimento", "tags": ["lideranca"]},
    )
    await client.post(
        "/api/v1/voters",
        headers=headers,
        json={"name": "Bruno Lima", "legal_basis": "consentimento", "tags": ["voluntario"]},
    )

    list_response = await client.get("/api/v1/voters", headers=headers)
    assert list_response.status_code == 200
    body = list_response.json()
    assert body["total"] == 2
    assert {item["name"] for item in body["items"]} == {"Ana Souza", "Bruno Lima"}

    filtered_response = await client.get("/api/v1/voters", headers=headers, params={"tags": ["lideranca"]})
    filtered_body = filtered_response.json()
    assert filtered_body["total"] == 1
    assert filtered_body["items"][0]["name"] == "Ana Souza"


async def test_update_voter_partial(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Voters - Update")

    create_response = await client.post(
        "/api/v1/voters",
        headers=headers,
        json={"name": "Carlos Souza", "legal_basis": "consentimento", "phone": "65911112222"},
    )
    voter_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/voters/{voter_id}", headers=headers, json={"phone": "65933334444"}
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["phone"] == "65933334444"
    assert updated["name"] == "Carlos Souza"  # não foi alterado


async def test_delete_voter_then_404(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Voters - Delete")

    create_response = await client.post(
        "/api/v1/voters", headers=headers, json={"name": "Eleitor a Excluir", "legal_basis": "consentimento"}
    )
    voter_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/voters/{voter_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/voters/{voter_id}", headers=headers)
    assert get_response.status_code == 404


async def test_cannot_access_voter_from_another_tenant(client: AsyncClient) -> None:
    """Teste central de isolamento no nível de API, equivalente ao já feito para users no Módulo 1."""
    _, headers_a = await _register_and_login(client, tenant_name="Campanha Voters A - Isolamento")
    _, headers_b = await _register_and_login(client, tenant_name="Campanha Voters B - Isolamento")

    create_response = await client.post(
        "/api/v1/voters",
        headers=headers_a,
        json={"name": "Eleitor do Tenant A", "legal_basis": "consentimento"},
    )
    voter_id = create_response.json()["id"]

    # Tenant B, autenticado com seu próprio token válido, tenta acessar um
    # eleitor que existe, mas pertence ao tenant A.
    response = await client.get(f"/api/v1/voters/{voter_id}", headers=headers_b)
    assert response.status_code == 404  # não "existe" do ponto de vista do tenant B
