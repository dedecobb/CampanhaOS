"""
Schemas Pydantic dos endpoints de eventos (Agenda).
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

EventType = Literal["evento", "reuniao", "visita"]
EventStatus = Literal["agendado", "concluido", "cancelado"]


class EventCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    event_type: EventType
    starts_at: datetime
    description: str | None = None
    location: str | None = Field(None, max_length=500)
    ends_at: datetime | None = None
    # Se omitido, o router assume o próprio usuário autenticado como
    # responsável (conveniência: a maioria dos eventos é agendada pela
    # mesma pessoa que vai executá-los).
    responsible_user_id: UUID | None = None
    voter_id: UUID | None = None
    leadership_id: UUID | None = None


class EventUpdateRequest(BaseModel):
    """
    Atualização parcial (PATCH). `voter_id`/`leadership_id` aceitam `None`
    como valor válido (remover associação) — o router usa
    `model_fields_set` para diferenciar "omitido" de "enviado como null",
    mesmo padrão do módulo de Eleitores.
    """

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    event_type: EventType | None = None
    status: EventStatus | None = None
    location: str | None = Field(None, max_length=500)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    responsible_user_id: UUID | None = None
    voter_id: UUID | None = None
    leadership_id: UUID | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by_user_id: UUID
    responsible_user_id: UUID
    title: str
    description: str | None
    event_type: str
    status: str
    location: str | None
    starts_at: datetime
    ends_at: datetime | None
    voter_id: UUID | None
    leadership_id: UUID | None
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[EventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
