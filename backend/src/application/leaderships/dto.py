from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CreateLeadershipInput:
    tenant_id: UUID
    created_by_user_id: UUID
    name: str
    influence_level: str
    region: str | None = None
    estimated_votes: int = 0
    team_size: int | None = None
    notes: str | None = None


@dataclass(frozen=True)
class UpdateLeadershipInput:
    tenant_id: UUID
    leadership_id: UUID
    name: str | None = None
    region: str | None = None
    estimated_votes: int | None = None
    influence_level: str | None = None
    team_size: int | None = None
    notes: str | None = None


@dataclass(frozen=True)
class GetLeadershipInput:
    tenant_id: UUID
    leadership_id: UUID


@dataclass(frozen=True)
class DeleteLeadershipInput:
    tenant_id: UUID
    leadership_id: UUID


@dataclass(frozen=True)
class ListLeadershipsInput:
    tenant_id: UUID
    search_text: str | None = None
    influence_level: str | None = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class LeadershipOutput:
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


@dataclass(frozen=True)
class ListLeadershipsOutput:
    items: list[LeadershipOutput]
    total: int
    page: int
    page_size: int
    total_pages: int
