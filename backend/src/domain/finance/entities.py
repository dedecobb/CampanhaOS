"""
Entidade de domínio: FinanceTransaction (lançamento financeiro).

RF-12 (Fase 1): receitas, despesas e doações da campanha.

Decisão crítica: `amount` é `Decimal`, nunca `float` — dinheiro não pode
usar ponto flutuante binário, que não representa a maioria dos valores
decimais com exatidão (ex: 0.1 + 0.2 != 0.3 em float). Em milhares de
lançamentos, esse erro se acumula e gera divergência de caixa real.

`amount` é sempre armazenado POSITIVO — é o campo `type` que determina se
o valor soma ou subtrai num relatório (RN implícita: receita e doação
somam, despesa subtrai). Isso evita a ambiguidade de "valor negativo
representando uma despesa", que é fácil de inverter por engano em algum
cálculo futuro.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.shared.exceptions import DomainError, InvalidNameError

_VALID_TRANSACTION_TYPES = frozenset({"receita", "despesa", "doacao"})


class InvalidTransactionTypeError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(
            f"Tipo de lançamento '{value}' inválido. Valores aceitos: {', '.join(sorted(_VALID_TRANSACTION_TYPES))}"
        )


class InvalidAmountError(DomainError):
    def __init__(self) -> None:
        super().__init__("O valor do lançamento precisa ser maior que zero")


@dataclass
class FinanceTransaction:
    id: UUID
    tenant_id: UUID
    created_by_user_id: UUID
    type: str
    category: str
    amount: Decimal
    description: str | None
    occurred_at: date
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @staticmethod
    def create(
        tenant_id: UUID,
        created_by_user_id: UUID,
        type: str,
        category: str,
        amount: Decimal,
        occurred_at: date,
        description: str | None = None,
    ) -> "FinanceTransaction":
        FinanceTransaction._validate_type(type)
        FinanceTransaction._validate_category(category)
        FinanceTransaction._validate_amount(amount)

        now = datetime.now(UTC)
        return FinanceTransaction(
            id=uuid4(),
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            type=type,
            category=category.strip(),
            amount=amount,
            description=description,
            occurred_at=occurred_at,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    @staticmethod
    def _validate_type(type_: str) -> None:
        if type_ not in _VALID_TRANSACTION_TYPES:
            raise InvalidTransactionTypeError(type_)

    @staticmethod
    def _validate_category(category: str) -> None:
        if not category or not category.strip():
            raise InvalidNameError("Categoria do lançamento não pode ser vazia")

    @staticmethod
    def _validate_amount(amount: Decimal) -> None:
        if amount <= 0:
            raise InvalidAmountError

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def signed_amount(self) -> Decimal:
        """
        Valor com sinal aplicado conforme o tipo — usado só para cálculo
        de saldo (nunca persistido; `amount` no banco é sempre positivo).
        """
        return -self.amount if self.type == "despesa" else self.amount

    def update_details(
        self,
        *,
        type: str | None = None,
        category: str | None = None,
        amount: Decimal | None = None,
        description: str | None = None,
        occurred_at: date | None = None,
    ) -> None:
        if type is not None:
            FinanceTransaction._validate_type(type)
            self.type = type
        if category is not None:
            FinanceTransaction._validate_category(category)
            self.category = category.strip()
        if amount is not None:
            FinanceTransaction._validate_amount(amount)
            self.amount = amount
        if description is not None:
            self.description = description or None
        if occurred_at is not None:
            self.occurred_at = occurred_at

        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)
