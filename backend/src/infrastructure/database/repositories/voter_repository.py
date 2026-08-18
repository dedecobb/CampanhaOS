"""
Implementação concreta de VoterRepository usando SQLAlchemy async.
"""

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.voters.entities import Voter
from src.domain.voters.repository import Page, VoterDashboardStats, VoterFilter, VoterRepository
from src.infrastructure.database.models import LeadershipModel, VoterModel


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
                city=voter.city,
                state=voter.state,
                postal_code=voter.postal_code,
                neighborhood=voter.neighborhood,
                gender=voter.gender,
                birth_date=voter.birth_date,
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
            existing.city = voter.city
            existing.state = voter.state
            existing.postal_code = voter.postal_code
            existing.neighborhood = voter.neighborhood
            existing.gender = voter.gender
            existing.birth_date = voter.birth_date
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

    async def get_dashboard_stats(self, tenant_id: UUID) -> VoterDashboardStats:
        base_conditions = (VoterModel.tenant_id == tenant_id, VoterModel.deleted_at.is_(None))

        total_stmt = select(func.count()).select_from(VoterModel).where(*base_conditions)
        total = (await self._session.execute(total_stmt)).scalar_one()

        # Gênero: agrupa direto pelo valor da coluna — None vira "nao_informado"
        # já na hora de montar o dicionário (não no SQL), mais simples.
        gender_stmt = select(VoterModel.gender, func.count()).where(*base_conditions).group_by(VoterModel.gender)
        gender_rows = (await self._session.execute(gender_stmt)).all()
        gender_breakdown = {(row[0] or "nao_informado"): row[1] for row in gender_rows}

        # Idade: calculada a partir de birth_date usando a função age() do
        # próprio Postgres (mais precisa que "ano atual - ano de
        # nascimento", já considera se o aniversário já passou este ano),
        # depois classificada em faixas via CASE — tudo no banco, nunca
        # carregando eleitor por eleitor pra calcular em Python.
        age_years = func.extract("year", func.age(func.current_date(), VoterModel.birth_date))
        age_bracket = case(
            (VoterModel.birth_date.is_(None), "nao_informado"),
            (age_years.between(16, 17), "16-17"),
            (age_years.between(18, 24), "18-24"),
            (age_years.between(25, 34), "25-34"),
            (age_years.between(35, 44), "35-44"),
            (age_years.between(45, 59), "45-59"),
            (age_years >= 60, "60+"),
            else_="nao_informado",
        )
        age_stmt = select(age_bracket, func.count()).where(*base_conditions).group_by(age_bracket)
        age_rows = (await self._session.execute(age_stmt)).all()
        age_breakdown = {row[0]: row[1] for row in age_rows}

        # Crescimento: últimos 30 dias, agrupado por dia do cadastro.
        thirty_days_ago = date.today() - timedelta(days=30)
        growth_stmt = (
            select(func.date(VoterModel.created_at), func.count())
            .where(*base_conditions, VoterModel.created_at >= thirty_days_ago)
            .group_by(func.date(VoterModel.created_at))
            .order_by(func.date(VoterModel.created_at))
        )
        growth_rows = (await self._session.execute(growth_stmt)).all()
        registration_growth = [(row[0], row[1]) for row in growth_rows]

        # Origem: autocadastro (created_by_user_id NULO) vs. cadastrado
        # pela equipe (created_by_user_id preenchido).
        origin = case((VoterModel.created_by_user_id.is_(None), "autocadastro"), else_="equipe")
        origin_stmt = select(origin, func.count()).where(*base_conditions).group_by(origin)
        origin_rows = (await self._session.execute(origin_stmt)).all()
        origin_map = {row[0]: row[1] for row in origin_rows}

        # Liderança: LEFT JOIN pra incluir também quem NÃO tem liderança
        # vinculada (leadership_id NULL) — esses caem no grupo "Sem
        # liderança" em vez de sumir da contagem.
        leadership_stmt = (
            select(LeadershipModel.name, func.count())
            .select_from(VoterModel)
            .outerjoin(LeadershipModel, VoterModel.leadership_id == LeadershipModel.id)
            .where(*base_conditions)
            .group_by(LeadershipModel.name)
            .order_by(func.count().desc())
        )
        leadership_rows = (await self._session.execute(leadership_stmt)).all()
        leadership_breakdown = [(name or "Sem liderança", count) for name, count in leadership_rows]

        return VoterDashboardStats(
            total=total,
            gender_breakdown=gender_breakdown,
            age_breakdown=age_breakdown,
            registration_growth=registration_growth,
            self_registered_count=origin_map.get("autocadastro", 0),
            staff_registered_count=origin_map.get("equipe", 0),
            leadership_breakdown=leadership_breakdown,
        )

    async def list_with_coordinates(self, tenant_id: UUID, limit: int = 1000) -> list[Voter]:
        stmt = (
            select(VoterModel)
            .where(
                VoterModel.tenant_id == tenant_id,
                VoterModel.deleted_at.is_(None),
                VoterModel.latitude.is_not(None),
                VoterModel.longitude.is_not(None),
            )
            .order_by(VoterModel.name.asc())
            .limit(limit)
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: VoterModel) -> Voter:
        return Voter(
            id=model.id,
            tenant_id=model.tenant_id,
            created_by_user_id=model.created_by_user_id,
            name=model.name,
            phone=model.phone,
            address=model.address,
            city=model.city,
            state=model.state,
            postal_code=model.postal_code,
            neighborhood=model.neighborhood,
            gender=model.gender,
            birth_date=model.birth_date,
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
