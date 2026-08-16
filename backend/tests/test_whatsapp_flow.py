"""
Testes de integração do módulo WhatsApp (nível de API).

IMPORTANTE: estes testes exigem `TWILIO_AUTH_TOKEN` configurado no `.env`
local (não precisa ser um token real do Twilio — só precisa ser
consistente, já que os próprios testes calculam a assinatura esperada
usando esse mesmo valor). Sem essa variável, o webhook responde 503
("WhatsApp não configurado") para tudo, e os testes que dependem de
verificação de assinatura de verdade seriam pulados/falhariam.

Sugestão de linha para o `.env` (nunca use isso em produção):
    TWILIO_AUTH_TOKEN=test_twilio_auth_token_dev
"""

import base64
import hashlib
import hmac
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.settings import get_settings

_WEBHOOK_PATH = "/api/v1/whatsapp/webhook"


def _unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@campanhaos.dev"


async def _register_tenant_and_login(client: AsyncClient, *, tenant_name: str) -> tuple[str, dict[str, str]]:
    email = _unique_email("whatsapp")
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


def _build_twilio_signature(auth_token: str, full_url: str, params: dict[str, str]) -> str:
    """Réplica do algoritmo do Twilio, usada só para MONTAR requisições de teste válidas."""
    data = full_url
    for key in sorted(params.keys()):
        data += key + params[key]
    return base64.b64encode(hmac.new(auth_token.encode(), data.encode(), hashlib.sha1).digest()).decode()


def _skip_if_twilio_not_configured() -> None:
    settings = get_settings()
    if not settings.twilio_auth_token:
        pytest.skip("TWILIO_AUTH_TOKEN não configurado no .env — ver docstring do arquivo")


async def test_webhook_with_valid_signature_creates_opt_in(client: AsyncClient, db_session: AsyncSession) -> None:
    _skip_if_twilio_not_configured()
    settings = get_settings()

    tenant_id, headers = await _register_tenant_and_login(client, tenant_name="Campanha WhatsApp Opt-in")

    full_url = f"http://test{_WEBHOOK_PATH}?tenant_id={tenant_id}"
    params = {"From": "whatsapp:+5521999998888", "Body": "Oi, quero saber mais sobre a campanha"}
    signature = _build_twilio_signature(settings.twilio_auth_token, full_url, params)

    response = await client.post(
        full_url,
        data=params,
        headers={"X-Twilio-Signature": signature},
    )
    assert response.status_code == 200, response.text

    contacts_response = await client.get("/api/v1/whatsapp/contacts", headers=headers)
    assert contacts_response.status_code == 200
    contacts = contacts_response.json()
    assert len(contacts) == 1
    assert contacts[0]["phone_number"] == "+5521999998888"


async def test_webhook_with_invalid_signature_returns_403(client: AsyncClient) -> None:
    _skip_if_twilio_not_configured()

    tenant_id, _headers = await _register_tenant_and_login(client, tenant_name="Campanha WhatsApp Assinatura Falsa")

    full_url = f"http://test{_WEBHOOK_PATH}?tenant_id={tenant_id}"
    response = await client.post(
        full_url,
        data={"From": "whatsapp:+5521999998888", "Body": "oi"},
        headers={"X-Twilio-Signature": "assinatura_forjada_qualquer_coisa="},
    )
    assert response.status_code == 403


async def test_webhook_with_nonexistent_tenant_returns_404(client: AsyncClient) -> None:
    _skip_if_twilio_not_configured()

    fake_tenant_id = uuid.uuid4()
    full_url = f"http://test{_WEBHOOK_PATH}?tenant_id={fake_tenant_id}"
    response = await client.post(
        full_url,
        data={"From": "whatsapp:+5521999998888", "Body": "oi"},
        headers={"X-Twilio-Signature": "qualquer_coisa="},
    )
    assert response.status_code == 404


async def test_webhook_opt_out_keyword_processes_opt_out(client: AsyncClient, db_session: AsyncSession) -> None:
    _skip_if_twilio_not_configured()
    settings = get_settings()

    tenant_id, headers = await _register_tenant_and_login(client, tenant_name="Campanha WhatsApp Opt-out")

    async def send_webhook(body: str) -> None:
        full_url = f"http://test{_WEBHOOK_PATH}?tenant_id={tenant_id}"
        params = {"From": "whatsapp:+5521888887777", "Body": body}
        signature = _build_twilio_signature(settings.twilio_auth_token, full_url, params)
        response = await client.post(full_url, data=params, headers={"X-Twilio-Signature": signature})
        assert response.status_code == 200, response.text

    await send_webhook("Oi")
    await send_webhook("PARAR")

    contacts_response = await client.get("/api/v1/whatsapp/contacts", headers=headers)
    contacts = contacts_response.json()
    # opt-out -> não aparece mais na listagem de contatos ATIVOS
    assert len(contacts) == 0


async def test_list_whatsapp_contacts_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/api/v1/whatsapp/contacts")
    assert response.status_code == 401


async def test_send_whatsapp_message_requires_auth(client: AsyncClient) -> None:
    response = await client.post("/api/v1/whatsapp/send", json={"contact_id": str(uuid.uuid4()), "template_sid": "HX123"})
    assert response.status_code == 401


async def test_send_to_non_opted_in_contact_returns_403(client: AsyncClient, db_session: AsyncSession) -> None:
    """
    O teste mais importante do módulo: prova que a trava de compliance
    (nunca enviar sem opt-in ativo) funciona de ponta a ponta pela API
    real, não só no caso de uso isolado (já testado no Bloco C).
    """
    _skip_if_twilio_not_configured()
    settings = get_settings()

    tenant_id, headers = await _register_tenant_and_login(client, tenant_name="Campanha WhatsApp Sem Opt-in")
    full_url = f"http://test{_WEBHOOK_PATH}?tenant_id={tenant_id}"
    phone = "whatsapp:+5521777776666"

    async def send_webhook(body: str) -> None:
        params = {"From": phone, "Body": body}
        signature = _build_twilio_signature(settings.twilio_auth_token, full_url, params)
        response = await client.post(full_url, data=params, headers={"X-Twilio-Signature": signature})
        assert response.status_code == 200, response.text

    # 1. Cria o opt-in
    await send_webhook("Oi, quero saber mais")

    # 2. Captura o id do contato ENQUANTO ele ainda está opt-in — é a
    # única forma de conseguir esse id, já que a listagem só mostra
    # contatos ativos.
    contacts_response = await client.get("/api/v1/whatsapp/contacts", headers=headers)
    contact_id = contacts_response.json()[0]["id"]

    # 3. Contato pede pra sair
    await send_webhook("PARAR")

    # 4. Tenta enviar mensagem pro MESMO contato (que existe, mas não
    # está mais opt-in) — deve ser bloqueado com 403, não 404.
    send_response = await client.post(
        "/api/v1/whatsapp/send",
        headers=headers,
        json={"contact_id": contact_id, "template_sid": "HX123"},
    )
    assert send_response.status_code == 403, send_response.text


async def test_send_to_nonexistent_contact_returns_404(client: AsyncClient) -> None:
    _, headers = await _register_tenant_and_login(client, tenant_name="Campanha WhatsApp Contato Inexistente")

    response = await client.post(
        "/api/v1/whatsapp/send",
        headers=headers,
        json={"contact_id": str(uuid.uuid4()), "template_sid": "HX123"},
    )
    assert response.status_code == 404, response.text
