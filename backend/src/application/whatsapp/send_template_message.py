from src.application.whatsapp.dto import SendWhatsAppTemplateMessageInput, SendWhatsAppTemplateMessageOutput
from src.application.whatsapp.exceptions import ContactNotOptedInError, WhatsAppContactNotFoundError
from src.application.whatsapp.ports import WhatsAppSenderPort
from src.domain.whatsapp.repository import WhatsAppContactRepository


class SendWhatsAppTemplateMessageUseCase:
    def __init__(
        self,
        whatsapp_contact_repository: WhatsAppContactRepository,
        whatsapp_sender: WhatsAppSenderPort,
    ) -> None:
        self._whatsapp_contact_repository = whatsapp_contact_repository
        self._whatsapp_sender = whatsapp_sender

    async def execute(self, input_data: SendWhatsAppTemplateMessageInput) -> SendWhatsAppTemplateMessageOutput:
        contact = await self._whatsapp_contact_repository.find_by_id(input_data.tenant_id, input_data.contact_id)
        if contact is None:
            raise WhatsAppContactNotFoundError

        # ESSA é a trava de compliance mais importante do módulo inteiro
        # — nenhum caminho de código consegue enviar mensagem pra um
        # contato sem opt-in ativo, independente de quem chamar este
        # caso de uso ou com quais parâmetros.
        if not contact.is_opted_in:
            raise ContactNotOptedInError

        success = await self._whatsapp_sender.send_template_message(
            to_phone_number=contact.phone_number,
            template_sid=input_data.template_sid,
            template_variables=input_data.template_variables,
        )
        return SendWhatsAppTemplateMessageOutput(success=success)
