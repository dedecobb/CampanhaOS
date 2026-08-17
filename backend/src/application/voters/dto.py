"""
DTOs dos casos de uso de eleitores.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any
from uuid import UUID


class _Unset:
    """
    Sentinela para distinguir "campo não foi informado" de "campo foi
    informado como None" — necessário para `leadership_id` em
    UpdateVoterInput, onde `None` é um valor válido (remover a
    associação). Exportado (não prefixado com `_`) porque a camada de
    apresentação (router) também precisa dele, para traduzir corretamente
    a semântica de PATCH parcial do JSON recebido.
    """

    def __repr__(self) -> str:
        return "UNSET"


UNSET: Any = _Unset()


@dataclass(frozen=True)
class CreateVoterInput:
    tenant_id: UUID
    created_by_user_id: UUID
    name: str
    legal_basis: str
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    neighborhood: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    latitude: float | None = None
    longitude: float | None = None
    tags: list[str] = field(default_factory=list)
    custom_fields: dict[str, str] = field(default_factory=dict)
    notes: str | None = None
    leadership_id: UUID | None = None


@dataclass(frozen=True)
class UpdateVoterInput:
    tenant_id: UUID
    voter_id: UUID
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    neighborhood: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    latitude: float | None = None
    longitude: float | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, str] | None = None
    notes: str | None = None
    leadership_id: UUID | None = UNSET  # type: ignore[assignment]


@dataclass(frozen=True)
class GetVoterInput:
    tenant_id: UUID
    voter_id: UUID


@dataclass(frozen=True)
class DeleteVoterInput:
    tenant_id: UUID
    voter_id: UUID


@dataclass(frozen=True)
class ListVotersInput:
    tenant_id: UUID
    search_text: str | None = None
    tags: list[str] | None = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class ListVotersForMapInput:
    tenant_id: UUID


@dataclass(frozen=True)
class VoterOutput:
    id: UUID
    created_by_user_id: UUID | None
    name: str
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    neighborhood: str | None
    gender: str | None
    birth_date: date | None
    latitude: float | None
    longitude: float | None
    tags: list[str]
    custom_fields: dict[str, str]
    notes: str | None
    legal_basis: str
    created_at: datetime
    updated_at: datetime
    leadership_id: UUID | None


@dataclass(frozen=True)
class ListVotersOutput:
    items: list[VoterOutput]
    total: int
    page: int
    page_size: int
    total_pages: int


@dataclass(frozen=True)
class VoterMapPointOutput:
    """
    Saída LEVE de propósito — só os campos necessários para desenhar um
    pino no mapa. Reaproveitar `VoterOutput` inteiro traria campos como
    `tags`/`custom_fields`/`notes` que o mapa nunca usa, inflando o
    payload à toa quando há muitos eleitores geocodificados.
    """

    id: UUID
    name: str
    address: str | None
    latitude: float
    longitude: float
