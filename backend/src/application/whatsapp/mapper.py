from src.application.whatsapp.dto import WhatsAppContactOutput
from src.domain.whatsapp.entities import WhatsAppContact


def contact_to_output(contact: WhatsAppContact) -> WhatsAppContactOutput:
    return WhatsAppContactOutput(
        id=contact.id,
        phone_number=contact.phone_number,
        voter_id=contact.voter_id,
        opted_in_at=contact.opted_in_at,
        opt_in_source=contact.opt_in_source,
    )
