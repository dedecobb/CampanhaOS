"""
Porta (interface) do repositório de Tenant.

Corrige uma lacuna do Bloco A: a interface de User foi criada, mas a de
Tenant ficou faltando — só percebida ao desenhar o caso de uso de
registro de campanha, que precisa salvar um Tenant. Registrado no
documento fonte da verdade como aprendizado do processo.

`list_paginated` foi adicionado no Módulo 7 — até então, nenhum caso de
uso precisava listar tenants (cada tenant só enxerga a si mesmo). O
painel de super-admin é o primeiro consumidor dessa capacidade.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from src.domain.tenants.entities import Tenant


@dataclass(frozen=True)
class TenantFilter:
    search_text: str | None = None  # busca por nome


@dataclass(frozen=True)
class TenantPage:
    items: list[Tenant]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class TenantRepository(ABC):
    @abstractmethod
    async def save(self, tenant: Tenant) -> None:
        """Persiste um tenant novo ou atualiza um existente (upsert por id)."""

    @abstractmethod
    async def find_by_id(self, tenant_id: UUID) -> Tenant | None:
        """
        Busca por id. Diferente de `UserRepository.find_by_id`, aqui não há
        um "tenant pai" para escopar — Tenant é a raiz do isolamento, não
        algo isolado por outra coisa.
        """

    @abstractmethod
    async def list_paginated(self, filters: TenantFilter, page: int, page_size: int) -> TenantPage:
        """
        Sem escopo de tenant (não faria sentido — é justamente a listagem
        DE tenants). Usado exclusivamente pelo painel de super-admin.
        """

    @abstractmethod
    async def find_by_registration_token(self, token: str) -> Tenant | None:
        """
        Usado pelo endpoint PÚBLICO de autocadastro (sem login) — a única
        forma de identificar de qual campanha é um cadastro público é
        através desse token, não do tenant_id diretamente.
        """
