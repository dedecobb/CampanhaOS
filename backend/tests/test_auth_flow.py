"""
Testes de integração do fluxo de autenticação (nível de API).

Roda contra a aplicação real (via ASGITransport, sem precisar de um
servidor HTTP de verdade rodando), que por sua vez fala com PostgreSQL e
Redis reais.
"""

import uuid

from httpx import AsyncClient


def _unique_email(prefix: str) -> str:
    # Cada teste usa um e-mail único para nunca colidir com execuções
    # anteriores da suíte contra o mesmo banco (não fazemos limpeza entre
    # execuções locais de propósito — cada tenant criado é isolado por
    # natureza, então não há necessidade de truncar tabelas entre testes).
    return f"{prefix}-{uuid.uuid4().hex[:8]}@teste.campanhaos.dev"


async def _register_tenant(client: AsyncClient, *, tenant_name: str, email: str) -> dict:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": tenant_name,
            "admin_name": "Admin de Teste",
            "admin_email": email,
            "admin_password": "senha_forte_123",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_register_login_me_flow(client: AsyncClient) -> None:
    email = _unique_email("fluxo-completo")

    register_data = await _register_tenant(client, tenant_name="Campanha Teste E2E", email=email)
    assert "tenant_id" in register_data
    assert "user_id" in register_data

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_id": register_data["tenant_id"], "email": email, "password": "senha_forte_123"},
    )
    assert login_response.status_code == 200, login_response.text
    tokens = login_response.json()
    assert tokens["token_type"] == "bearer"
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    me_response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert me_response.status_code == 200, me_response.text
    me_data = me_response.json()
    assert me_data["id"] == register_data["user_id"]
    assert me_data["tenant_id"] == register_data["tenant_id"]
    assert me_data["email"] == email.lower()


async def test_login_with_wrong_password_fails(client: AsyncClient) -> None:
    email = _unique_email("senha-errada")
    register_data = await _register_tenant(client, tenant_name="Campanha Senha Errada", email=email)

    response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_id": register_data["tenant_id"], "email": email, "password": "senha_totalmente_errada"},
    )
    assert response.status_code == 401


async def test_register_with_weak_password_fails(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "Campanha Senha Fraca",
            "admin_name": "Admin",
            "admin_email": _unique_email("senha-fraca"),
            "admin_password": "123",
        },
    )
    assert response.status_code == 422


async def test_me_without_token_fails(client: AsyncClient) -> None:
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_refresh_token_rotation(client: AsyncClient) -> None:
    email = _unique_email("refresh-rotacao")
    register_data = await _register_tenant(client, tenant_name="Campanha Refresh", email=email)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_id": register_data["tenant_id"], "email": email, "password": "senha_forte_123"},
    )
    original_refresh_token = login_response.json()["refresh_token"]

    # Primeiro uso: deve funcionar e retornar um par novo.
    refresh_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": original_refresh_token}
    )
    assert refresh_response.status_code == 200, refresh_response.text
    new_tokens = refresh_response.json()
    assert new_tokens["refresh_token"] != original_refresh_token

    # Reuso do token antigo: deve ser rejeitado (rotação/revogação).
    reuse_response = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": original_refresh_token}
    )
    assert reuse_response.status_code == 401


async def test_cannot_login_by_mixing_email_with_another_tenant_id(client: AsyncClient) -> None:
    """
    Teste central de isolamento no nível de API: um e-mail válido, mas
    combinado com o tenant_id de OUTRO tenant, nunca deve autenticar —
    mesmo que a senha esteja correta para aquele usuário no tenant certo.
    """
    email = _unique_email("cruzamento-tenant")
    tenant_a = await _register_tenant(client, tenant_name="Campanha A - Isolamento", email=email)

    outro_email = _unique_email("tenant-b-admin")
    tenant_b = await _register_tenant(client, tenant_name="Campanha B - Isolamento", email=outro_email)

    # Login correto: e-mail do usuário do tenant A, mas informando o
    # tenant_id do tenant B. Mesmo a senha estando "certa" para esse
    # e-mail dentro do tenant A, a busca do usuário é escopada ao tenant B
    # informado — onde esse e-mail não existe.
    response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_id": tenant_b["tenant_id"], "email": email, "password": "senha_forte_123"},
    )
    assert response.status_code == 401
