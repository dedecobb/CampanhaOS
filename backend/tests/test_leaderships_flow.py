"""
Testes de integração do módulo de Lideranças (nível de API) e da
associação Eleitor <-> Liderança.
"""

import uuid

from httpx import AsyncClient


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@teste.campanhaos.dev"


async def _register_and_login(client: AsyncClient, *, tenant_name: str) -> tuple[str, dict[str, str]]:
    email = _unique_email("leaderships")
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


# --- CRUD de lideranças ---


async def test_create_and_get_leadership(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Leaderships - Create")

    create_response = await client.post(
        "/api/v1/leaderships",
        headers=headers,
        json={"name": "José das Neves", "influence_level": "alta", "region": "Zona Norte", "estimated_votes": 150},
    )
    assert create_response.status_code == 201, create_response.text
    leadership = create_response.json()
    assert leadership["name"] == "José das Neves"
    assert leadership["estimated_votes"] == 150

    get_response = await client.get(f"/api/v1/leaderships/{leadership['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == leadership["id"]


async def test_create_leadership_with_invalid_influence_level_returns_422(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Leaderships - Nível Inválido")

    response = await client.post(
        "/api/v1/leaderships",
        headers=headers,
        json={"name": "Liderança Teste", "influence_level": "nivel_inventado"},
    )
    assert response.status_code == 422


async def test_leadership_endpoints_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/leaderships")
    assert response.status_code == 401


async def test_list_and_filter_leaderships(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Leaderships - Listagem")

    await client.post(
        "/api/v1/leaderships", headers=headers, json={"name": "Liderança Alta", "influence_level": "alta"}
    )
    await client.post(
        "/api/v1/leaderships", headers=headers, json={"name": "Liderança Baixa", "influence_level": "baixa"}
    )

    list_response = await client.get("/api/v1/leaderships", headers=headers)
    assert list_response.json()["total"] == 2

    filtered_response = await client.get(
        "/api/v1/leaderships", headers=headers, params={"influence_level": "alta"}
    )
    filtered_body = filtered_response.json()
    assert filtered_body["total"] == 1
    assert filtered_body["items"][0]["name"] == "Liderança Alta"


async def test_update_leadership_partial(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Leaderships - Update")

    create_response = await client.post(
        "/api/v1/leaderships",
        headers=headers,
        json={"name": "Liderança Original", "influence_level": "media", "estimated_votes": 50},
    )
    leadership_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/leaderships/{leadership_id}", headers=headers, json={"estimated_votes": 100}
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["estimated_votes"] == 100
    assert updated["name"] == "Liderança Original"


async def test_delete_leadership_then_404(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Leaderships - Delete")

    create_response = await client.post(
        "/api/v1/leaderships", headers=headers, json={"name": "Liderança a Excluir", "influence_level": "baixa"}
    )
    leadership_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/leaderships/{leadership_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/leaderships/{leadership_id}", headers=headers)
    assert get_response.status_code == 404


async def test_cannot_access_leadership_from_another_tenant(client: AsyncClient) -> None:
    _, headers_a = await _register_and_login(client, tenant_name="Campanha Leaderships A - Isolamento")
    _, headers_b = await _register_and_login(client, tenant_name="Campanha Leaderships B - Isolamento")

    create_response = await client.post(
        "/api/v1/leaderships",
        headers=headers_a,
        json={"name": "Liderança do Tenant A", "influence_level": "alta"},
    )
    leadership_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/leaderships/{leadership_id}", headers=headers_b)
    assert response.status_code == 404


# --- Associação Eleitor <-> Liderança ---


async def test_create_voter_with_leadership_association(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Associação - Create")

    leadership_response = await client.post(
        "/api/v1/leaderships", headers=headers, json={"name": "Liderança Y", "influence_level": "alta"}
    )
    leadership_id = leadership_response.json()["id"]

    voter_response = await client.post(
        "/api/v1/voters",
        headers=headers,
        json={"name": "Eleitor Associado", "legal_basis": "consentimento", "leadership_id": leadership_id},
    )
    assert voter_response.status_code == 201, voter_response.text
    assert voter_response.json()["leadership_id"] == leadership_id


async def test_create_voter_with_nonexistent_leadership_returns_404(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Associação - Inexistente")

    response = await client.post(
        "/api/v1/voters",
        headers=headers,
        json={
            "name": "Eleitor Órfão",
            "legal_basis": "consentimento",
            "leadership_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 404


async def test_update_voter_to_associate_and_then_disassociate_leadership(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Associação - Update")

    leadership_response = await client.post(
        "/api/v1/leaderships", headers=headers, json={"name": "Liderança Z", "influence_level": "media"}
    )
    leadership_id = leadership_response.json()["id"]

    voter_response = await client.post(
        "/api/v1/voters", headers=headers, json={"name": "Eleitor Sem Liderança", "legal_basis": "consentimento"}
    )
    voter_id = voter_response.json()["id"]
    assert voter_response.json()["leadership_id"] is None

    # Associa
    associate_response = await client.patch(
        f"/api/v1/voters/{voter_id}", headers=headers, json={"leadership_id": leadership_id}
    )
    assert associate_response.json()["leadership_id"] == leadership_id

    # Um PATCH que não menciona leadership_id não deve desfazer a associação
    rename_response = await client.patch(
        f"/api/v1/voters/{voter_id}", headers=headers, json={"name": "Eleitor Renomeado"}
    )
    assert rename_response.json()["leadership_id"] == leadership_id

    # Desassocia explicitamente (null)
    disassociate_response = await client.patch(
        f"/api/v1/voters/{voter_id}", headers=headers, json={"leadership_id": None}
    )
    assert disassociate_response.json()["leadership_id"] is None


async def test_cannot_associate_voter_with_leadership_from_another_tenant(client: AsyncClient) -> None:
    _, headers_a = await _register_and_login(client, tenant_name="Campanha Associação Cruzada A")
    _, headers_b = await _register_and_login(client, tenant_name="Campanha Associação Cruzada B")

    leadership_response = await client.post(
        "/api/v1/leaderships", headers=headers_a, json={"name": "Liderança Exclusiva A", "influence_level": "alta"}
    )
    leadership_id_from_a = leadership_response.json()["id"]

    # Tenant B tenta criar um eleitor associando a uma liderança que só
    # existe no tenant A.
    response = await client.post(
        "/api/v1/voters",
        headers=headers_b,
        json={
            "name": "Eleitor do Tenant B",
            "legal_basis": "consentimento",
            "leadership_id": leadership_id_from_a,
        },
    )
    assert response.status_code == 404
