"""
Porta (interface) do repositório de Leadership.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from src.domain.leaderships.entities import Leadership


@dataclass(frozen=True)
class LeadershipFilter:
    search_text: str | None = None  # busca em nome/região
    influence_level: str | None = None
    include_deleted: bool = False


@dataclass(frozen=True)
class LeadershipPage:
    items: list[Leadership]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class LeadershipRepository(ABC):
    @abstractmethod
    async def save(self, leadership: Leadership) -> None:
        """Persiste uma liderança nova ou atualiza uma existente (upsert por id)."""

    @abstractmethod
    async def find_by_id(self, tenant_id: UUID, leadership_id: UUID) -> Leadership | None:
        """Busca por id, escopado ao tenant."""

    @abstractmethod
    async def exists(self, tenant_id: UUID, leadership_id: UUID) -> bool:
        """
        Checagem leve de existência, usada pela validação cross-entity no
        módulo de Eleitores (confirmar que um leadership_id associado a um
        Voter realmente existe e pertence ao mesmo tenant, sem precisar
        carregar o objeto Leadership inteiro).
        """

    @abstractmethod
    async def list_paginated(
        self,
        tenant_id: UUID,
        filters: LeadershipFilter,
        page: int,
        page_size: int,
    ) -> LeadershipPage:
        """Lista paginada, página 1-indexada (mesmo padrão de VoterRepository)."""
