"""
Porta (interface) do repositório de FinanceTransaction.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from uuid import UUID

from src.domain.finance.entities import FinanceTransaction


@dataclass(frozen=True)
class FinanceFilter:
    type: str | None = None
    category: str | None = None
    occurred_after: date | None = None
    occurred_before: date | None = None
    include_deleted: bool = False


@dataclass(frozen=True)
class FinancePage:
    items: list[FinanceTransaction]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.page_size == 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


@dataclass(frozen=True)
class FinanceSummary:
    total_receitas: Decimal
    total_despesas: Decimal
    total_doacoes: Decimal

    @property
    def saldo(self) -> Decimal:
        return self.total_receitas + self.total_doacoes - self.total_despesas


class FinanceRepository(ABC):
    @abstractmethod
    async def save(self, transaction: FinanceTransaction) -> None:
        """Persiste um lançamento novo ou atualiza um existente (upsert por id)."""

    @abstractmethod
    async def find_by_id(self, tenant_id: UUID, transaction_id: UUID) -> FinanceTransaction | None:
        """Busca por id, escopado ao tenant."""

    @abstractmethod
    async def list_paginated(
        self,
        tenant_id: UUID,
        filters: FinanceFilter,
        page: int,
        page_size: int,
    ) -> FinancePage:
        """Lista paginada, mais recentes primeiro (por `occurred_at`)."""

    @abstractmethod
    async def get_summary(self, tenant_id: UUID, filters: FinanceFilter) -> FinanceSummary:
        """
        Totais agregados (soma por tipo) respeitando os MESMOS filtros da
        listagem — calculado via agregação no banco (SUM/GROUP BY), não
        somando em Python, para não precisar carregar todos os registros
        na memória só para totalizar.
        """
