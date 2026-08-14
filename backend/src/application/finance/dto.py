from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class CreateFinanceTransactionInput:
    tenant_id: UUID
    created_by_user_id: UUID
    type: str
    category: str
    amount: Decimal
    occurred_at: date
    description: str | None = None


@dataclass(frozen=True)
class UpdateFinanceTransactionInput:
    tenant_id: UUID
    transaction_id: UUID
    type: str | None = None
    category: str | None = None
    amount: Decimal | None = None
    description: str | None = None
    occurred_at: date | None = None


@dataclass(frozen=True)
class GetFinanceTransactionInput:
    tenant_id: UUID
    transaction_id: UUID


@dataclass(frozen=True)
class DeleteFinanceTransactionInput:
    tenant_id: UUID
    transaction_id: UUID


@dataclass(frozen=True)
class ListFinanceTransactionsInput:
    tenant_id: UUID
    type: str | None = None
    category: str | None = None
    occurred_after: date | None = None
    occurred_before: date | None = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class FinanceTransactionOutput:
    id: UUID
    created_by_user_id: UUID
    type: str
    category: str
    amount: Decimal
    description: str | None
    occurred_at: date
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FinanceSummaryOutput:
    total_receitas: Decimal
    total_despesas: Decimal
    total_doacoes: Decimal
    saldo: Decimal


@dataclass(frozen=True)
class ListFinanceTransactionsOutput:
    items: list[FinanceTransactionOutput]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: FinanceSummaryOutput
