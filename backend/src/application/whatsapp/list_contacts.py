from src.application.whatsapp.dto import ListWhatsAppContactsInput, WhatsAppContactOutput
from src.application.whatsapp.mapper import contact_to_output
from src.domain.whatsapp.repository import WhatsAppContactRepository


class ListWhatsAppContactsUseCase:
    def __init__(self, whatsapp_contact_repository: WhatsAppContactRepository) -> None:
        self._whatsapp_contact_repository = whatsapp_contact_repository

    async def execute(self, input_data: ListWhatsAppContactsInput) -> list[WhatsAppContactOutput]:
        contacts = await self._whatsapp_contact_repository.list_opted_in(input_data.tenant_id)
        return [contact_to_output(c) for c in contacts]
