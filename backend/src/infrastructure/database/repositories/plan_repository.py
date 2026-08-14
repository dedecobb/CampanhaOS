"""
Implementação concreta de PlanRepository usando SQLAlchemy async.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.billing.entities import Plan
from src.domain.billing.repository import PlanRepository
from src.infrastructure.database.models import PlanModel


class SqlAlchemyPlanRepository(PlanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, plan: Plan) -> None:
        existing = await self._session.get(PlanModel, plan.id)
        if existing is None:
            model = PlanModel(
                id=plan.id,
                name=plan.name,
                price=plan.price,
                max_users=plan.max_users,
                max_voters=plan.max_voters,
                is_active=plan.is_active,
            )
            self._session.add(model)
        else:
            existing.name = plan.name
            existing.price = plan.price
            existing.max_users = plan.max_users
            existing.max_voters = plan.max_voters
            existing.is_active = plan.is_active

        await self._session.flush()

    async def find_by_id(self, plan_id: UUID) -> Plan | None:
        model = await self._session.get(PlanModel, plan_id)
        return self._to_domain(model) if model else None

    async def exists_active(self, plan_id: UUID) -> bool:
        stmt = select(PlanModel.id).where(PlanModel.id == plan_id, PlanModel.is_active.is_(True))
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        return result is not None

    async def list_all(self, *, only_active: bool = False) -> list[Plan]:
        stmt = select(PlanModel).order_by(PlanModel.price.asc())
        if only_active:
            stmt = stmt.where(PlanModel.is_active.is_(True))
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: PlanModel) -> Plan:
        return Plan(
            id=model.id,
            name=model.name,
            price=model.price,
            max_users=model.max_users,
            max_voters=model.max_voters,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
