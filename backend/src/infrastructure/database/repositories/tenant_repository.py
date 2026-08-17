"""
Implementação concreta de TenantRepository, paralela ao
SqlAlchemyUserRepository do Bloco B.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tenants.entities import Tenant, TenantStatus
from src.domain.tenants.repository import TenantFilter, TenantPage, TenantRepository
from src.infrastructure.database.models import TenantModel


class SqlAlchemyTenantRepository(TenantRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, tenant: Tenant) -> None:
        existing = await self._session.get(TenantModel, tenant.id)
        if existing is None:
            model = TenantModel(
                id=tenant.id,
                name=tenant.name,
                status=tenant.status.value,
                public_registration_token=tenant.public_registration_token,
                voter_goal=tenant.voter_goal,
            )
            self._session.add(model)
        else:
            existing.name = tenant.name
            existing.status = tenant.status.value
            existing.public_registration_token = tenant.public_registration_token
            existing.voter_goal = tenant.voter_goal

        await self._session.flush()

    async def find_by_id(self, tenant_id: UUID) -> Tenant | None:
        model = await self._session.get(TenantModel, tenant_id)
        if model is None:
            return None
        return self._to_domain(model)

    async def find_by_registration_token(self, token: str) -> Tenant | None:
        stmt = select(TenantModel).where(TenantModel.public_registration_token == token)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_paginated(self, filters: TenantFilter, page: int, page_size: int) -> TenantPage:
        conditions = []
        if filters.search_text:
            conditions.append(TenantModel.name.ilike(f"%{filters.search_text}%"))

        count_stmt = select(func.count()).select_from(TenantModel).where(*conditions)
        total = (await self._session.execute(count_stmt)).scalar_one()

        list_stmt = (
            select(TenantModel)
            .where(*conditions)
            .order_by(TenantModel.name.asc(), TenantModel.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = (await self._session.execute(list_stmt)).scalars().all()

        return TenantPage(
            items=[self._to_domain(m) for m in models],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _to_domain(self, model: TenantModel) -> Tenant:
        return Tenant(
            id=model.id,
            name=model.name,
            status=TenantStatus(model.status),
            created_at=model.created_at,
            public_registration_token=model.public_registration_token,
            voter_goal=model.voter_goal,
        )
