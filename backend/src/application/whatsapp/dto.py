from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class HandleIncomingWhatsAppMessageInput:
    tenant_id: UUID
    phone_number: str  # já normalizado em formato E.164 pelo webhook
    message_body: str


@dataclass(frozen=True)
class SendWhatsAppTemplateMessageInput:
    tenant_id: UUID
    contact_id: UUID
    template_sid: str
    template_variables: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class SendWhatsAppTemplateMessageOutput:
    success: bool


@dataclass(frozen=True)
class ListWhatsAppContactsInput:
    tenant_id: UUID


@dataclass(frozen=True)
class WhatsAppContactOutput:
    id: UUID
    phone_number: str
    voter_id: UUID | None
    opted_in_at: datetime
    opt_in_source: str
