"""
Caso de uso central de compliance deste módulo: toda mensagem recebida
passa por aqui antes de qualquer outra coisa.
"""

from src.application.whatsapp.dto import HandleIncomingWhatsAppMessageInput
from src.domain.whatsapp.entities import WhatsAppContact
from src.domain.whatsapp.repository import WhatsAppContactRepository

# Palavras que, em qualquer mensagem recebida, disparam descadastro
# automático — exigência explícita da Resolução TSE (RN: mensagem deve
# "oferecer uma forma simples para o eleitor solicitar o
# descadastramento"). Checagem case-insensitive, ignorando espaços nas
# pontas.
_OPT_OUT_KEYWORDS = frozenset({"parar", "sair", "stop", "cancelar", "descadastrar", "não quero mais"})


class HandleIncomingWhatsAppMessageUseCase:
    def __init__(self, whatsapp_contact_repository: WhatsAppContactRepository) -> None:
        self._whatsapp_contact_repository = whatsapp_contact_repository

    async def execute(self, input_data: HandleIncomingWhatsAppMessageInput) -> None:
        is_opt_out_request = input_data.message_body.strip().lower() in _OPT_OUT_KEYWORDS

        contact = await self._whatsapp_contact_repository.find_by_phone_number(
            input_data.tenant_id, input_data.phone_number
        )

        if contact is None:
            if is_opt_out_request:
                # Pedido de descadastro de um número que nunca deu
                # opt-in — não há nada a fazer, mas também não criamos
                # um registro só pra imediatamente marcá-lo como saído.
                return
            contact = WhatsAppContact.create(tenant_id=input_data.tenant_id, phone_number=input_data.phone_number)
        elif is_opt_out_request:
            contact.opt_out()
        elif not contact.is_opted_in:
            # Contato tinha saído antes e voltou a mandar mensagem —
            # conta como novo consentimento válido (mesma regra do TSE:
            # precisa ser o contato iniciando, e é exatamente o que
            # está acontecendo aqui).
            contact.opt_in_again()

        await self._whatsapp_contact_repository.save(contact)
