"""
Implementação concreta de LeadershipRepository usando SQLAlchemy async.
"""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.leaderships.entities import Leadership
from src.domain.leaderships.repository import LeadershipFilter, LeadershipPage, LeadershipRepository
from src.infrastructure.database.models import LeadershipModel


class SqlAlchemyLeadershipRepository(LeadershipRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, leadership: Leadership) -> None:
        existing = await self._session.get(LeadershipModel, leadership.id)
        if existing is None:
            model = LeadershipModel(
                id=leadership.id,
                tenant_id=leadership.tenant_id,
                created_by_user_id=leadership.created_by_user_id,
                name=leadership.name,
                region=leadership.region,
                estimated_votes=leadership.estimated_votes,
                influence_level=leadership.influence_level,
                team_size=leadership.team_size,
                notes=leadership.notes,
                deleted_at=leadership.deleted_at,
            )
            self._session.add(model)
        else:
            existing.name = leadership.name
            existing.region = leadership.region
            existing.estimated_votes = leadership.estimated_votes
            existing.influence_level = leadership.influence_level
            existing.team_size = leadership.team_size
            existing.notes = leadership.notes
            existing.deleted_at = leadership.deleted_at

        await self._session.flush()

    async def find_by_id(self, tenant_id: UUID, leadership_id: UUID) -> Leadership | None:
        stmt = select(LeadershipModel).where(
            LeadershipModel.id == leadership_id,
            LeadershipModel.tenant_id == tenant_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def exists(self, tenant_id: UUID, leadership_id: UUID) -> bool:
        stmt = select(LeadershipModel.id).where(
            LeadershipModel.id == leadership_id,
            LeadershipModel.tenant_id == tenant_id,
            LeadershipModel.deleted_at.is_(None),
        )
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        return result is not None

    async def list_paginated(
        self,
        tenant_id: UUID,
        filters: LeadershipFilter,
        page: int,
        page_size: int,
    ) -> LeadershipPage:
        conditions = [LeadershipModel.tenant_id == tenant_id]

        if not filters.include_deleted:
            conditions.append(LeadershipModel.deleted_at.is_(None))

        if filters.search_text:
            pattern = f"%{filters.search_text}%"
            conditions.append(
                or_(LeadershipModel.name.ilike(pattern), LeadershipModel.region.ilike(pattern))
            )

        if filters.influence_level:
            conditions.append(LeadershipModel.influence_level == filters.influence_level)

        count_stmt = select(func.count()).select_from(LeadershipModel).where(*conditions)
        total = (await self._session.execute(count_stmt)).scalar_one()

        list_stmt = (
            select(LeadershipModel)
            .where(*conditions)
            .order_by(LeadershipModel.name.asc(), LeadershipModel.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = (await self._session.execute(list_stmt)).scalars().all()

        return LeadershipPage(
            items=[self._to_domain(m) for m in models],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _to_domain(self, model: LeadershipModel) -> Leadership:
        return Leadership(
            id=model.id,
            tenant_id=model.tenant_id,
            created_by_user_id=model.created_by_user_id,
            name=model.name,
            region=model.region,
            estimated_votes=model.estimated_votes,
            influence_level=model.influence_level,
            team_size=model.team_size,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
        )
