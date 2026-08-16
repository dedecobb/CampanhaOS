"""
Router WhatsApp.

O endpoint de webhook é DIFERENTE de todo outro endpoint do projeto até
agora: é público (o Twilio precisa conseguir chamá-lo sem JWT nosso), e
por isso NÃO usa `CurrentUser` — o que significa que ele precisa
declarar o contexto de tenant (RLS) manualmente, em vez de ganhar isso de
graça via `get_current_user` (Módulo 1). A segurança aqui vem da
verificação de assinatura do Twilio, não de autenticação JWT.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status

from src.application.whatsapp.dto import (
    HandleIncomingWhatsAppMessageInput,
    ListWhatsAppContactsInput,
    SendWhatsAppTemplateMessageInput,
)
from src.application.whatsapp.handle_incoming_message import HandleIncomingWhatsAppMessageUseCase
from src.application.whatsapp.list_contacts import ListWhatsAppContactsUseCase
from src.application.whatsapp.send_template_message import SendWhatsAppTemplateMessageUseCase
from src.config.settings import Settings, get_settings
from src.domain.tenants.repository import TenantRepository
from src.infrastructure.database.session import set_tenant_context
from src.infrastructure.whatsapp.twilio_signature import validate_twilio_signature
from src.presentation.api.admin_dependencies import get_tenant_repository_for_admin
from src.presentation.api.dependencies import CurrentUser, DbSession
from src.presentation.api.v1.schemas.whatsapp import (
    SendWhatsAppTemplateRequest,
    SendWhatsAppTemplateResponse,
    WhatsAppContactResponse,
)
from src.presentation.api.whatsapp_dependencies import (
    get_handle_incoming_whatsapp_message_use_case,
    get_list_whatsapp_contacts_use_case,
    get_send_whatsapp_template_message_use_case,
)

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def whatsapp_webhook(
    request: Request,
    session: DbSession,
    use_case: Annotated[
        HandleIncomingWhatsAppMessageUseCase, Depends(get_handle_incoming_whatsapp_message_use_case)
    ],
    tenant_repository: Annotated[TenantRepository, Depends(get_tenant_repository_for_admin)],
    settings: Annotated[Settings, Depends(get_settings)],
    tenant_id: UUID = Query(
        ..., description="Definido manualmente na configuração do webhook no painel do Twilio, um por campanha"
    ),
) -> Response:
    """
    Endpoint público — SEM CurrentUser de propósito. A Meta/Twilio chama
    isso sem nenhum JWT nosso. A verificação de assinatura do Twilio (não
    autenticação de usuário) é o que garante que a requisição é legítima.
    """
    tenant = await tenant_repository.find_by_id(tenant_id)
    if tenant is None:
        # 404 aqui é seguro de expor — não vaza nenhum dado sensível, só
        # confirma que esse tenant_id específico na URL não existe.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant não encontrado")

    form = await request.form()
    post_params = {key: str(value) for key, value in form.items()}

    if not settings.twilio_auth_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="WhatsApp não configurado")

    signature_header = request.headers.get("X-Twilio-Signature", "")
    full_url = str(request.url)
    is_valid_signature = validate_twilio_signature(
        settings.twilio_auth_token, full_url, post_params, signature_header
    )
    if not is_valid_signature:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Assinatura inválida")

    # A partir daqui, declara o contexto de tenant manualmente — sem
    # `CurrentUser`, ninguém fez isso por nós ainda (ver docstring do
    # arquivo). `whatsapp_contacts` tem RLS, precisa disso antes de
    # qualquer leitura/escrita.
    await set_tenant_context(session, tenant_id)

    from_number = post_params.get("From", "").removeprefix("whatsapp:")
    message_body = post_params.get("Body", "")

    if from_number:
        await use_case.execute(
            HandleIncomingWhatsAppMessageInput(
                tenant_id=tenant_id, phone_number=from_number, message_body=message_body
            )
        )
        await session.commit()

    # Twilio aceita 200 com corpo vazio como "recebido, sem resposta
    # automática" — não precisamos devolver TwiML.
    return Response(status_code=status.HTTP_200_OK)


@router.get("/contacts", response_model=list[WhatsAppContactResponse])
async def list_whatsapp_contacts(
    current_user: CurrentUser,
    use_case: Annotated[ListWhatsAppContactsUseCase, Depends(get_list_whatsapp_contacts_use_case)],
) -> list[WhatsAppContactResponse]:
    outputs = await use_case.execute(ListWhatsAppContactsInput(tenant_id=current_user.tenant_id))
    return [WhatsAppContactResponse.model_validate(o) for o in outputs]


@router.post("/send", response_model=SendWhatsAppTemplateResponse)
async def send_whatsapp_template_message(
    current_user: CurrentUser,
    request: SendWhatsAppTemplateRequest,
    use_case: Annotated[SendWhatsAppTemplateMessageUseCase, Depends(get_send_whatsapp_template_message_use_case)],
) -> SendWhatsAppTemplateResponse:
    output = await use_case.execute(
        SendWhatsAppTemplateMessageInput(
            tenant_id=current_user.tenant_id,
            contact_id=request.contact_id,
            template_sid=request.template_sid,
            template_variables=request.template_variables,
        )
    )
    return SendWhatsAppTemplateResponse(success=output.success)
