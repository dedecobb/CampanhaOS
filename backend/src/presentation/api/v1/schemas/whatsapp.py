"""
Schemas Pydantic dos endpoints de WhatsApp.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class WhatsAppContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    phone_number: str
    voter_id: UUID | None
    opted_in_at: datetime
    opt_in_source: str


class SendWhatsAppTemplateRequest(BaseModel):
    contact_id: UUID
    template_sid: str = Field(..., min_length=1, description="Content SID do template aprovado no Twilio")
    template_variables: dict[str, str] = Field(default_factory=dict)


class SendWhatsAppTemplateResponse(BaseModel):
    success: bool
