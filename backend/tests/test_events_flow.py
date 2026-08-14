"""
Testes de integração do módulo de Agenda (nível de API).
"""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@teste.campanhaos.dev"


async def _register_and_login(client: AsyncClient, *, tenant_name: str) -> tuple[str, dict[str, str]]:
    email = _unique_email("events")
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


def _future_iso(hours_from_now: int = 24) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours_from_now)).isoformat()


# --- CRUD básico ---


async def test_create_and_get_event(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Create")

    create_response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={"title": "Reunião Semanal", "event_type": "reuniao", "starts_at": _future_iso()},
    )
    assert create_response.status_code == 201, create_response.text
    event = create_response.json()
    assert event["title"] == "Reunião Semanal"
    assert event["status"] == "agendado"

    get_response = await client.get(f"/api/v1/events/{event['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["id"] == event["id"]


async def test_create_event_defaults_responsible_to_current_user(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Responsável Padrão")

    me_response = await client.get("/api/v1/auth/me", headers=headers)
    my_user_id = me_response.json()["id"]

    create_response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={"title": "Evento Sem Responsável Explícito", "event_type": "evento", "starts_at": _future_iso()},
    )
    assert create_response.json()["responsible_user_id"] == my_user_id


async def test_create_event_with_invalid_event_type_returns_422(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Tipo Inválido")

    response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={"title": "Evento Teste", "event_type": "tipo_inventado", "starts_at": _future_iso()},
    )
    assert response.status_code == 422


async def test_create_event_with_ends_before_starts_returns_422(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Período Inválido")

    starts_at = _future_iso(hours_from_now=48)
    ends_at = _future_iso(hours_from_now=24)  # antes do início — inválido

    response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={"title": "Evento Inválido", "event_type": "evento", "starts_at": starts_at, "ends_at": ends_at},
    )
    assert response.status_code == 422


async def test_create_event_with_nonexistent_responsible_user_returns_404(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Responsável Inexistente")

    response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Evento Órfão",
            "event_type": "evento",
            "starts_at": _future_iso(),
            "responsible_user_id": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 404


async def test_event_endpoints_require_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/events")
    assert response.status_code == 401


async def test_list_and_filter_events(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Listagem")

    await client.post(
        "/api/v1/events",
        headers=headers,
        json={"title": "Reunião A", "event_type": "reuniao", "starts_at": _future_iso(24)},
    )
    await client.post(
        "/api/v1/events",
        headers=headers,
        json={"title": "Visita B", "event_type": "visita", "starts_at": _future_iso(48)},
    )

    list_response = await client.get("/api/v1/events", headers=headers)
    assert list_response.json()["total"] == 2

    filtered_response = await client.get("/api/v1/events", headers=headers, params={"event_type": "visita"})
    filtered_body = filtered_response.json()
    assert filtered_body["total"] == 1
    assert filtered_body["items"][0]["title"] == "Visita B"


async def test_update_event_partial(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Update")

    create_response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={"title": "Evento Original", "event_type": "evento", "starts_at": _future_iso()},
    )
    event_id = create_response.json()["id"]

    update_response = await client.patch(
        f"/api/v1/events/{event_id}", headers=headers, json={"status": "concluido"}
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["status"] == "concluido"
    assert updated["title"] == "Evento Original"


async def test_delete_event_then_404(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Delete")

    create_response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={"title": "Evento a Excluir", "event_type": "evento", "starts_at": _future_iso()},
    )
    event_id = create_response.json()["id"]

    delete_response = await client.delete(f"/api/v1/events/{event_id}", headers=headers)
    assert delete_response.status_code == 204

    get_response = await client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert get_response.status_code == 404


async def test_cannot_access_event_from_another_tenant(client: AsyncClient) -> None:
    _, headers_a = await _register_and_login(client, tenant_name="Campanha Events A - Isolamento")
    _, headers_b = await _register_and_login(client, tenant_name="Campanha Events B - Isolamento")

    create_response = await client.post(
        "/api/v1/events",
        headers=headers_a,
        json={"title": "Evento do Tenant A", "event_type": "evento", "starts_at": _future_iso()},
    )
    event_id = create_response.json()["id"]

    response = await client.get(f"/api/v1/events/{event_id}", headers=headers_b)
    assert response.status_code == 404


# --- Associação com Eleitor e Liderança ---


async def test_event_with_voter_and_leadership_association(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Associação")

    voter_response = await client.post(
        "/api/v1/voters", headers=headers, json={"name": "Eleitor a Visitar", "legal_basis": "consentimento"}
    )
    voter_id = voter_response.json()["id"]

    leadership_response = await client.post(
        "/api/v1/leaderships", headers=headers, json={"name": "Liderança da Reunião", "influence_level": "alta"}
    )
    leadership_id = leadership_response.json()["id"]

    create_response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Visita ao Eleitor",
            "event_type": "visita",
            "starts_at": _future_iso(),
            "voter_id": voter_id,
            "leadership_id": leadership_id,
        },
    )
    assert create_response.status_code == 201, create_response.text
    event = create_response.json()
    assert event["voter_id"] == voter_id
    assert event["leadership_id"] == leadership_id


async def test_update_event_disassociate_voter_and_leadership(client: AsyncClient) -> None:
    _, headers = await _register_and_login(client, tenant_name="Campanha Events - Desassociação")

    voter_response = await client.post(
        "/api/v1/voters", headers=headers, json={"name": "Eleitor X", "legal_basis": "consentimento"}
    )
    voter_id = voter_response.json()["id"]

    create_response = await client.post(
        "/api/v1/events",
        headers=headers,
        json={
            "title": "Visita Programada",
            "event_type": "visita",
            "starts_at": _future_iso(),
            "voter_id": voter_id,
        },
    )
    event_id = create_response.json()["id"]

    # Update que não menciona voter_id preserva a associação
    rename_response = await client.patch(
        f"/api/v1/events/{event_id}", headers=headers, json={"title": "Visita Renomeada"}
    )
    assert rename_response.json()["voter_id"] == voter_id

    # Desassocia explicitamente
    disassociate_response = await client.patch(
        f"/api/v1/events/{event_id}", headers=headers, json={"voter_id": None}
    )
    assert disassociate_response.json()["voter_id"] is None
