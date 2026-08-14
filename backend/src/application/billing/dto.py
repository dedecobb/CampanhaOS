from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


class _Unset:
    def __repr__(self) -> str:
        return "UNSET"


UNSET: Any = _Unset()


@dataclass(frozen=True)
class CreatePlanInput:
    name: str
    price: Decimal
    max_users: int | None = None
    max_voters: int | None = None


@dataclass(frozen=True)
class UpdatePlanInput:
    plan_id: UUID
    name: str | None = None
    price: Decimal | None = None
    max_users: int | None = UNSET  # type: ignore[assignment]
    max_voters: int | None = UNSET  # type: ignore[assignment]


@dataclass(frozen=True)
class GetPlanInput:
    plan_id: UUID


@dataclass(frozen=True)
class ListPlansInput:
    only_active: bool = False


@dataclass(frozen=True)
class SetPlanActiveInput:
    plan_id: UUID


@dataclass(frozen=True)
class PlanOutput:
    id: UUID
    name: str
    price: Decimal
    max_users: int | None
    max_voters: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AssignSubscriptionInput:
    tenant_id: UUID
    plan_id: UUID
    current_period_end: date


@dataclass(frozen=True)
class GetSubscriptionInput:
    tenant_id: UUID


@dataclass(frozen=True)
class SubscriptionOutput:
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: str
    current_period_end: date
    created_at: datetime
    updated_at: datetime
