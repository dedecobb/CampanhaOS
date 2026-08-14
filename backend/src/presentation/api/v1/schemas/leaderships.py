"""
Schemas Pydantic dos endpoints de lideranças.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Espelha o conjunto de níveis válidos do domínio (src/domain/leaderships/entities.py).
InfluenceLevel = Literal["baixa", "media", "alta"]


class LeadershipCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    influence_level: InfluenceLevel
    region: str | None = Field(None, max_length=255)
    estimated_votes: int = Field(0, ge=0)
    team_size: int | None = Field(None, ge=0)
    notes: str | None = None


class LeadershipUpdateRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    region: str | None = Field(None, max_length=255)
    estimated_votes: int | None = Field(None, ge=0)
    influence_level: InfluenceLevel | None = None
    team_size: int | None = Field(None, ge=0)
    notes: str | None = None


class LeadershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by_user_id: UUID
    name: str
    region: str | None
    estimated_votes: int
    influence_level: str
    team_size: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class LeadershipListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[LeadershipResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
