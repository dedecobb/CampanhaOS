"""
Schemas Pydantic dos endpoints financeiros (Financeiro básico).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

TransactionType = Literal["receita", "despesa", "doacao"]


class FinanceTransactionCreateRequest(BaseModel):
    type: TransactionType
    category: str = Field(..., min_length=1, max_length=255)
    amount: Decimal = Field(..., gt=0, description="Sempre positivo — o tipo determina se soma ou subtrai")
    occurred_at: date
    description: str | None = None


class FinanceTransactionUpdateRequest(BaseModel):
    type: TransactionType | None = None
    category: str | None = Field(None, min_length=1, max_length=255)
    amount: Decimal | None = Field(None, gt=0)
    occurred_at: date | None = None
    description: str | None = None


class FinanceTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by_user_id: UUID
    type: str
    category: str
    amount: Decimal
    description: str | None
    occurred_at: date
    created_at: datetime
    updated_at: datetime


class FinanceSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_receitas: Decimal
    total_despesas: Decimal
    total_doacoes: Decimal
    saldo: Decimal


class FinanceTransactionListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[FinanceTransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: FinanceSummaryResponse
