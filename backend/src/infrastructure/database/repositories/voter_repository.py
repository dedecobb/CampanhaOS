"""
Implementação concreta de VoterRepository usando SQLAlchemy async.
"""

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.voters.entities import Voter
from src.domain.voters.repository import Page, VoterFilter, VoterRepository
from src.infrastructure.database.models import VoterModel


class SqlAlchemyVoterRepository(VoterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, voter: Voter) -> None:
        existing = await self._session.get(VoterModel, voter.id)
        if existing is None:
            model = VoterModel(
                id=voter.id,
                tenant_id=voter.tenant_id,
                created_by_user_id=voter.created_by_user_id,
                name=voter.name,
                phone=voter.phone,
                address=voter.address,
                latitude=voter.latitude,
                longitude=voter.longitude,
                tags=voter.tags,
                custom_fields=voter.custom_fields,
                notes=voter.notes,
                legal_basis=voter.legal_basis,
                deleted_at=voter.deleted_at,
                leadership_id=voter.leadership_id,
            )
            self._session.add(model)
        else:
            existing.name = voter.name
            existing.phone = voter.phone
            existing.address = voter.address
            existing.latitude = voter.latitude
            existing.longitude = voter.longitude
            existing.tags = voter.tags
            existing.custom_fields = voter.custom_fields
            existing.notes = voter.notes
            existing.deleted_at = voter.deleted_at
            existing.leadership_id = voter.leadership_id
            # legal_basis não é alterável via update_details (ver domínio) —
            # a base legal de um dado já coletado não muda retroativamente.

        await self._session.flush()

    async def find_by_id(self, tenant_id: UUID, voter_id: UUID) -> Voter | None:
        stmt = select(VoterModel).where(
            VoterModel.id == voter_id,
            VoterModel.tenant_id == tenant_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_paginated(
        self,
        tenant_id: UUID,
        filters: VoterFilter,
        page: int,
        page_size: int,
    ) -> Page:
        conditions = [VoterModel.tenant_id == tenant_id]

        if not filters.include_deleted:
            conditions.append(VoterModel.deleted_at.is_(None))

        if filters.search_text:
            pattern = f"%{filters.search_text}%"
            conditions.append(or_(VoterModel.name.ilike(pattern), VoterModel.phone.ilike(pattern)))

        if filters.tags:
            # Operador de containment do array do PostgreSQL (`@>`): o
            # eleitor precisa ter TODAS as tags do filtro, podendo ter
            # outras além dessas.
            conditions.append(VoterModel.tags.contains(filters.tags))

        count_stmt = select(func.count()).select_from(VoterModel).where(*conditions)
        total = (await self._session.execute(count_stmt)).scalar_one()

        list_stmt = (
            select(VoterModel)
            .where(*conditions)
            .order_by(VoterModel.name.asc(), VoterModel.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = (await self._session.execute(list_stmt)).scalars().all()

        return Page(
            items=[self._to_domain(m) for m in models],
            total=total,
            page=page,
            page_size=page_size,
        )

    def _to_domain(self, model: VoterModel) -> Voter:
        return Voter(
            id=model.id,
            tenant_id=model.tenant_id,
            created_by_user_id=model.created_by_user_id,
            name=model.name,
            phone=model.phone,
            address=model.address,
            latitude=model.latitude,
            longitude=model.longitude,
            tags=list(model.tags),
            custom_fields=dict(model.custom_fields),
            notes=model.notes,
            legal_basis=model.legal_basis,
            created_at=model.created_at,
            updated_at=model.updated_at,
            deleted_at=model.deleted_at,
            leadership_id=model.leadership_id,
        )
