from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PlanCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., ge=0)
    max_users: int | None = Field(None, gt=0, description="None = ilimitado")
    max_voters: int | None = Field(None, gt=0, description="None = ilimitado")


class PlanUpdateRequest(BaseModel):
    """
    `max_users`/`max_voters` aceitam `null` como valor válido
    (= ilimitado). O router usa `model_fields_set` para diferenciar
    "campo omitido" de "campo enviado como null" — mesmo padrão do
    módulo de Eleitores (Módulo 3).
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    price: Decimal | None = Field(None, ge=0)
    max_users: int | None = Field(None, gt=0)
    max_voters: int | None = Field(None, gt=0)


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    price: Decimal
    max_users: int | None
    max_voters: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AssignSubscriptionRequest(BaseModel):
    plan_id: UUID
    current_period_end: date


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    plan_id: UUID
    status: str
    current_period_end: date
    created_at: datetime
    updated_at: datetime
