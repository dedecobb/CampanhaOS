"""
Injeção de dependência (composition root) do módulo WhatsApp.
"""

from typing import Annotated

from fastapi import Depends

from src.application.whatsapp.handle_incoming_message import HandleIncomingWhatsAppMessageUseCase
from src.application.whatsapp.list_contacts import ListWhatsAppContactsUseCase
from src.application.whatsapp.ports import WhatsAppSenderPort
from src.application.whatsapp.send_template_message import SendWhatsAppTemplateMessageUseCase
from src.config.settings import Settings, get_settings
from src.infrastructure.database.repositories.whatsapp_contact_repository import SqlAlchemyWhatsAppContactRepository
from src.infrastructure.whatsapp.twilio_sender import TwilioWhatsAppSender
from src.presentation.api.dependencies import DbSession


def get_whatsapp_contact_repository(session: DbSession) -> SqlAlchemyWhatsAppContactRepository:
    return SqlAlchemyWhatsAppContactRepository(session)


def get_whatsapp_sender(settings: Annotated[Settings, Depends(get_settings)]) -> WhatsAppSenderPort:
    # Mesmo espírito de `get_geocoding_service` (Módulo de Mapa): se as
    # credenciais não estiverem configuradas, ainda assim construímos o
    # objeto (com strings vazias) — a falha acontece na hora de tentar
    # enviar de verdade, com erro claro, não na inicialização da aplicação.
    return TwilioWhatsAppSender(
        account_sid=settings.twilio_account_sid or "",
        auth_token=settings.twilio_auth_token or "",
        from_number=settings.twilio_whatsapp_from_number or "",
    )


WhatsAppContactRepositoryDep = Annotated[
    SqlAlchemyWhatsAppContactRepository, Depends(get_whatsapp_contact_repository)
]
WhatsAppSenderDep = Annotated[WhatsAppSenderPort, Depends(get_whatsapp_sender)]


def get_handle_incoming_whatsapp_message_use_case(
    whatsapp_contact_repository: WhatsAppContactRepositoryDep,
) -> HandleIncomingWhatsAppMessageUseCase:
    return HandleIncomingWhatsAppMessageUseCase(whatsapp_contact_repository)


def get_send_whatsapp_template_message_use_case(
    whatsapp_contact_repository: WhatsAppContactRepositoryDep,
    whatsapp_sender: WhatsAppSenderDep,
) -> SendWhatsAppTemplateMessageUseCase:
    return SendWhatsAppTemplateMessageUseCase(whatsapp_contact_repository, whatsapp_sender)


def get_list_whatsapp_contacts_use_case(
    whatsapp_contact_repository: WhatsAppContactRepositoryDep,
) -> ListWhatsAppContactsUseCase:
    return ListWhatsAppContactsUseCase(whatsapp_contact_repository)
