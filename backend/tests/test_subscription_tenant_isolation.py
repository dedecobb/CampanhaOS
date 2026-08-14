"""
Testes de isolamento de tenant no nível de banco (RLS) para
`subscriptions` — mesmo padrão de todos os testes de isolamento
anteriores no projeto.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.billing.entities import Plan, Subscription
from src.domain.tenants.entities import Tenant
from src.infrastructure.database.repositories.plan_repository import SqlAlchemyPlanRepository
from src.infrastructure.database.repositories.subscription_repository import SqlAlchemySubscriptionRepository
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.database.session import set_tenant_context


async def _create_tenant_and_subscription(
    session: AsyncSession, *, tenant_name: str
) -> tuple[uuid.UUID, uuid.UUID]:
    tenant = Tenant.create(name=tenant_name)
    await SqlAlchemyTenantRepository(session).save(tenant)

    # `plans` não tem RLS — pode ser salvo sem contexto de tenant setado.
    plan = Plan.create(name=f"Plano {tenant_name}", price=Decimal("50.00"))
    await SqlAlchemyPlanRepository(session).save(plan)

    await set_tenant_context(session, tenant.id)
    subscription = Subscription.create(tenant_id=tenant.id, plan_id=plan.id, current_period_end=date(2026, 12, 1))
    await SqlAlchemySubscriptionRepository(session).save(subscription)

    await session.commit()
    return tenant.id, subscription.id


async def test_rls_blocks_cross_tenant_subscription_select(db_session: AsyncSession) -> None:
    tenant_a_id, subscription_a_id = await _create_tenant_and_subscription(
        db_session, tenant_name=f"RLS Subscription A {uuid.uuid4().hex[:8]}"
    )
    _tenant_b_id, subscription_b_id = await _create_tenant_and_subscription(
        db_session, tenant_name=f"RLS Subscription B {uuid.uuid4().hex[:8]}"
    )

    await set_tenant_context(db_session, tenant_a_id)
    result = await db_session.execute(text("SELECT id, tenant_id FROM subscriptions"))
    rows = result.fetchall()

    visible_ids = {row.id for row in rows}
    assert subscription_a_id in visible_ids
    assert subscription_b_id not in visible_ids, "VAZAMENTO: assinatura de outro tenant apareceu numa query sem filtro"
    assert all(row.tenant_id == tenant_a_id for row in rows)


async def test_rls_blocks_subscription_select_when_no_tenant_context_is_set(db_session: AsyncSession) -> None:
    await _create_tenant_and_subscription(db_session, tenant_name=f"RLS Subscription Sem Contexto {uuid.uuid4().hex[:8]}")

    result = await db_session.execute(text("SELECT id FROM subscriptions"))
    assert result.fetchall() == [], "sem contexto de tenant, deveria retornar zero linhas (fail-closed)"


async def test_rls_blocks_subscription_insert_with_mismatched_tenant_id(db_session: AsyncSession) -> None:
    tenant_a_id, _ = await _create_tenant_and_subscription(
        db_session, tenant_name=f"RLS Subscription Insert A {uuid.uuid4().hex[:8]}"
    )

    # Precisa de um plan_id válido (FK), mas o objetivo é provar que o
    # RLS bloqueia ANTES disso importar.
    plan = Plan.create(name="Plano Auxiliar", price=Decimal("10.00"))
    await SqlAlchemyPlanRepository(db_session).save(plan)
    await db_session.commit()

    fake_other_tenant_id = uuid.uuid4()
    await set_tenant_context(db_session, tenant_a_id)

    with pytest.raises(DBAPIError):
        await db_session.execute(
            text(
                """
                INSERT INTO subscriptions (id, tenant_id, plan_id, status, current_period_end)
                VALUES (:id, :tenant_id, :plan_id, 'active', CURRENT_DATE)
                """
            ),
            {"id": uuid.uuid4(), "tenant_id": fake_other_tenant_id, "plan_id": plan.id},
        )
