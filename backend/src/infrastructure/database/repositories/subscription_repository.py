"""
Implementação concreta de SubscriptionRepository usando SQLAlchemy async.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.billing.entities import Subscription
from src.domain.billing.repository import SubscriptionRepository
from src.infrastructure.database.models import SubscriptionModel


class SqlAlchemySubscriptionRepository(SubscriptionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, subscription: Subscription) -> None:
        existing = await self._session.get(SubscriptionModel, subscription.id)
        if existing is None:
            model = SubscriptionModel(
                id=subscription.id,
                tenant_id=subscription.tenant_id,
                plan_id=subscription.plan_id,
                status=subscription.status,
                current_period_end=subscription.current_period_end,
            )
            self._session.add(model)
        else:
            existing.plan_id = subscription.plan_id
            existing.status = subscription.status
            existing.current_period_end = subscription.current_period_end

        await self._session.flush()

    async def find_by_tenant_id(self, tenant_id: UUID) -> Subscription | None:
        stmt = select(SubscriptionModel).where(SubscriptionModel.tenant_id == tenant_id)
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: SubscriptionModel) -> Subscription:
        return Subscription(
            id=model.id,
            tenant_id=model.tenant_id,
            plan_id=model.plan_id,
            status=model.status,
            current_period_end=model.current_period_end,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
