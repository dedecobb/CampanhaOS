"""
Porta (interface) do repositório de Voter.

Inclui filtros e paginação na assinatura desde o início — dado o
requisito da Fase 1 de suportar milhões de registros, nunca teria sentido
um método `list_all()` sem paginação, então nem desenhamos a interface
permitindo isso.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from src.domain.voters.entities import Voter


@dataclass(frozen=True)
class VoterFilter:
    """
    Critérios de busca. Todos opcionais — quando None/vazio, o filtro
    correspondente não é aplicado.
    """

    search_text: str | None = None  # busca em nome/telefone
    tags: list[str] | None = None  # eleitor precisa ter TODAS as tags listadas
    include_deleted: bool = False


@dataclass(frozen=True)
class Page:
    items: list[Voter]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class VoterRepository(ABC):
    @abstractmethod
    async def save(self, voter: Voter) -> None:
        """Persiste um eleitor novo ou atualiza um existente (upsert por id)."""

    @abstractmethod
    async def find_by_id(self, tenant_id: UUID, voter_id: UUID) -> Voter | None:
        """Busca por id, escopado ao tenant (mesmo padrão do Módulo 1)."""

    @abstractmethod
    async def list_paginated(
        self,
        tenant_id: UUID,
        filters: VoterFilter,
        page: int,
        page_size: int,
    ) -> Page:
        """
        Lista paginada. `page` é 1-indexado (página 1 é a primeira, não a
        0) — convenção mais natural para quem consome a API depois.
        """

    @abstractmethod
    async def list_with_coordinates(self, tenant_id: UUID, limit: int = 1000) -> list[Voter]:
        """
        Usado pela tela de mapa — retorna eleitores com latitude/longitude
        preenchidas, SEM paginação de página em página (não faz sentido
        paginar pontos de um mapa), mas COM um teto explícito (`limit`).
        Isso não contradiz o princípio documentado acima ("nunca um
        list_all() sem limite") — só troca "paginação" por "teto fixo"
        como mecanismo de limitação, apropriado para este caso de uso
        específico (renderizar pontos num mapa, não navegar página a
        página por uma lista).
        """

