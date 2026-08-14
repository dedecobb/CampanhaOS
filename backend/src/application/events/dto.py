from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


class _Unset:
    def __repr__(self) -> str:
        return "UNSET"


UNSET: Any = _Unset()


@dataclass(frozen=True)
class CreateEventInput:
    tenant_id: UUID
    created_by_user_id: UUID
    responsible_user_id: UUID
    title: str
    event_type: str
    starts_at: datetime
    description: str | None = None
    location: str | None = None
    ends_at: datetime | None = None
    voter_id: UUID | None = None
    leadership_id: UUID | None = None


@dataclass(frozen=True)
class UpdateEventInput:
    tenant_id: UUID
    event_id: UUID
    title: str | None = None
    description: str | None = None
    event_type: str | None = None
    status: str | None = None
    location: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    responsible_user_id: UUID | None = None
    voter_id: UUID | None = UNSET  # type: ignore[assignment]
    leadership_id: UUID | None = UNSET  # type: ignore[assignment]


@dataclass(frozen=True)
class GetEventInput:
    tenant_id: UUID
    event_id: UUID


@dataclass(frozen=True)
class DeleteEventInput:
    tenant_id: UUID
    event_id: UUID


@dataclass(frozen=True)
class ListEventsInput:
    tenant_id: UUID
    search_text: str | None = None
    event_type: str | None = None
    status: str | None = None
    starts_after: datetime | None = None
    starts_before: datetime | None = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class EventOutput:
    id: UUID
    created_by_user_id: UUID
    responsible_user_id: UUID
    title: str
    description: str | None
    event_type: str
    status: str
    location: str | None
    starts_at: datetime
    ends_at: datetime | None
    voter_id: UUID | None
    leadership_id: UUID | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class ListEventsOutput:
    items: list[EventOutput]
    total: int
    page: int
    page_size: int
    total_pages: int
