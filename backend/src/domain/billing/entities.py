"""
Entidades de domínio: Plan e Subscription.

`Plan` é um catálogo GLOBAL (sem tenant_id) — mesmo padrão de `Permission`
(Módulo 1): o conjunto de planos que a plataforma oferece é o mesmo pra
todos os tenants, só a assinatura de cada um é que varia.

`Subscription` liga um tenant a um plano — TEM tenant_id, então segue o
mesmo padrão de RLS de toda tabela de negócio do projeto. Relação 1:1: um
tenant tem no máximo uma assinatura ativa por vez (histórico de mudança
de plano não é rastreado nesta versão — ver limitação registrada no
documento fonte da verdade).
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.shared.exceptions import DomainError, InvalidNameError

_VALID_SUBSCRIPTION_STATUSES = frozenset({"trialing", "active", "past_due", "canceled"})

_UNSET = object()  # sentinela: None é valor válido para max_users/max_voters (= ilimitado)


class InvalidPriceError(DomainError):
    def __init__(self) -> None:
        super().__init__("O preço do plano não pode ser negativo")


class InvalidPlanLimitError(DomainError):
    def __init__(self, field: str) -> None:
        super().__init__(f"O limite '{field}' precisa ser maior que zero, ou None para ilimitado")


class InvalidSubscriptionStatusError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(
            f"Status de assinatura '{value}' inválido. "
            f"Valores aceitos: {', '.join(sorted(_VALID_SUBSCRIPTION_STATUSES))}"
        )


@dataclass
class Plan:
    id: UUID
    name: str
    price: Decimal
    max_users: int | None  # None = ilimitado
    max_voters: int | None  # None = ilimitado
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        name: str,
        price: Decimal,
        max_users: int | None = None,
        max_voters: int | None = None,
    ) -> "Plan":
        Plan._validate_name(name)
        Plan._validate_price(price)
        Plan._validate_limit(max_users, "max_users")
        Plan._validate_limit(max_voters, "max_voters")

        now = datetime.now(UTC)
        return Plan(
            id=uuid4(),
            name=name.strip(),
            price=price,
            max_users=max_users,
            max_voters=max_voters,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise InvalidNameError("Nome do plano não pode ser vazio")

    @staticmethod
    def _validate_price(price: Decimal) -> None:
        if price < 0:
            raise InvalidPriceError

    @staticmethod
    def _validate_limit(value: int | None, field: str) -> None:
        if value is not None and value <= 0:
            raise InvalidPlanLimitError(field)

    def update_details(
        self,
        *,
        name: str | None = None,
        price: Decimal | None = None,
        max_users: int | None = _UNSET,  # type: ignore[assignment]
        max_voters: int | None = _UNSET,  # type: ignore[assignment]
    ) -> None:
        """
        `max_users`/`max_voters` usam o sentinela `_UNSET` pelo mesmo
        motivo de `Voter.leadership_id` (Módulo 3): `None` é um valor
        válido aqui (representa "ilimitado"), então não pode dobrar como
        "não foi informado".
        """
        if name is not None:
            Plan._validate_name(name)
            self.name = name.strip()
        if price is not None:
            Plan._validate_price(price)
            self.price = price
        if max_users is not _UNSET:
            Plan._validate_limit(max_users, "max_users")
            self.max_users = max_users
        if max_voters is not _UNSET:
            Plan._validate_limit(max_voters, "max_voters")
            self.max_voters = max_voters

        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Plano deixa de ser oferecido a novos tenants — assinaturas existentes não são afetadas."""
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(UTC)


@dataclass
class Subscription:
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: str
    current_period_end: date
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        tenant_id: UUID,
        plan_id: UUID,
        current_period_end: date,
        status: str = "trialing",
    ) -> "Subscription":
        Subscription._validate_status(status)

        now = datetime.now(UTC)
        return Subscription(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=plan_id,
            status=status,
            current_period_end=current_period_end,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in _VALID_SUBSCRIPTION_STATUSES:
            raise InvalidSubscriptionStatusError(status)

    def change_plan(self, new_plan_id: UUID) -> None:
        self.plan_id = new_plan_id
        self.updated_at = datetime.now(UTC)

    def update_status(self, status: str) -> None:
        Subscription._validate_status(status)
        self.status = status
        self.updated_at = datetime.now(UTC)

    def renew(self, new_period_end: date) -> None:
        self.current_period_end = new_period_end
        self.status = "active"
        self.updated_at = datetime.now(UTC)
