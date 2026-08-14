"""
Porta (interface) do repositório de Event.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.domain.events.entities import Event


@dataclass(frozen=True)
class EventFilter:
    search_text: str | None = None  # busca em título/descrição
    event_type: str | None = None
    status: str | None = None
    starts_after: datetime | None = None
    starts_before: datetime | None = None
    include_deleted: bool = False


@dataclass(frozen=True)
class EventPage:
    items: list[Event]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class EventRepository(ABC):
    @abstractmethod
    async def save(self, event: Event) -> None:
        """Persiste um evento novo ou atualiza um existente (upsert por id)."""

    @abstractmethod
    async def find_by_id(self, tenant_id: UUID, event_id: UUID) -> Event | None:
        """Busca por id, escopado ao tenant."""

    @abstractmethod
    async def list_paginated(
        self,
        tenant_id: UUID,
        filters: EventFilter,
        page: int,
        page_size: int,
    ) -> EventPage:
        """
        Lista paginada, página 1-indexada. Ordenação padrão por
        `starts_at` (mais próximos primeiro) — diferente de Voter/
        Leadership (ordenados por nome), porque agenda faz mais sentido
        cronologicamente do que alfabeticamente.
        """
