"""
Implementação concreta de EventRepository usando SQLAlchemy async.
"""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.events.entities import Event
from src.domain.events.repository import EventFilter, EventPage, EventRepository
from src.infrastructure.database.models import EventModel


class SqlAlchemyEventRepository(EventRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, event: Event) -> None:
        existing = await self._session.get(EventModel, event.id)
        if existing is None:
            model = EventModel(
                id=event.id,
                tenant_id=event.tenant_id,
                created_by_user_id=event.created_by_user_id,
                responsible_user_id=event.responsible_user_id,
                title=event.title,
                description=event.description,
                event_type=event.event_type,
                status=event.status,
                location=event.location,
                starts_at=event.starts_at,
                ends_at=event.ends_at,
                voter_id=event.voter_id,
                leadership_id=event.leadership_id,
                deleted_at=event.deleted_at,
            )
            self._session.add(model)
        else:
            existing.responsible_user_id = event.responsible_user_id
            existing.title = event.title
            existing.description = event.description
            existing.event_type = event.event_type
            existing.status = event.status
            existing.location = event.location
            existing.starts_at = event.starts_at
            existing.ends_at = event.ends_at
            existing.voter_id = event.voter_id
            existing.leadership_id = event.leadership_id
            existing.deleted_at = event.deleted_at

        await self._session.flush()

    async def find_by_id(self, tenant_id: UUID, event_id: UUID) -> Event | None:
        stmt = select(EventModel).where(
            EventModel.id == event_id,
            EventModel.tenant_id == tenant_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_paginated(
        self,
        tenant_id: UUID,
        filters: EventFilter,
        page: int,
        page_size: int,
    ) -> EventPage:
        conditions = [EventModel.tenant_id == tenant_id]

        if not filters.include_deleted:
            conditions.append(EventModel.deleted_at.is_(None))

        if filters.search_text:
            pattern = f"%{filters.search_text}%"
            conditions.append(or_(EventModel.title.ilike(pattern), EventModel.description.ilike(pattern)))

        if filters.event_type:
            conditions.append(EventModel.event_type == filters.event_type)

        if filters.status:
            conditions.append(EventModel.status == filters.status)

        if filters.starts_after:
            conditions.append(EventModel.starts_at >= filters.starts_after)

        if filters.starts_before:
            conditions.append(EventModel.starts_at <= filters.starts_before)

        count_stmt = select(func.count()).select_from(EventModel).where(*conditions)
        total = (await self._session.execute(count_stmt)).scalar_one()

        list_stmt = (
            select(EventModel)
            .where(*conditions)
            .order_by(EventModel.starts_at.asc(), EventModel.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = (await self._session.execute(list_stmt)).scalars().all()

        return EventPage(
            items=[self._to_domain(m) for m in models],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _to_domain(self, model: EventModel) -> Event:
        return Event(
            id=model.id,
            tenant_id=model.tenant_id,
            created_by_user_id=model.created_by_user_id,
            responsible_user_id=model.responsible_user_id,
            title=model.title,
            description=model.description,
            event_type=model.event_type,
            status=model.status,
            location=model.location,
            starts_at=model.starts_at,
            ends_at=model.ends_at,
            voter_id=model.voter_id,
            leadership_id=model.leadership_id,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
