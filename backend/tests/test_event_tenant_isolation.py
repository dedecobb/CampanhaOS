"""
Testes de isolamento de tenant no nível de banco (RLS) para `events`.

Mesmo padrão de todos os testes de isolamento anteriores no projeto.
"""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.events.entities import Event
from src.domain.tenants.entities import Tenant
from src.domain.users.entities import User
from src.domain.users.value_objects import Email
from src.infrastructure.database.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.database.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.database.session import set_tenant_context
from src.infrastructure.security.password_hasher import BcryptPasswordHasher


async def _create_tenant_user_and_event(
    session: AsyncSession, *, tenant_name: str, email: str, event_title: str
) -> tuple[uuid.UUID, uuid.UUID]:
    tenant = Tenant.create(name=tenant_name)
    await SqlAlchemyTenantRepository(session).save(tenant)
    await set_tenant_context(session, tenant.id)

    hasher = BcryptPasswordHasher()
    user = User.create(
        tenant_id=tenant.id,
        name="Usuário de Teste",
        email=Email(email),
        password_hash=hasher.hash("senha_forte_123"),
    )
    await SqlAlchemyUserRepository(session).save(user)

    event = Event.create(
        tenant_id=tenant.id,
        created_by_user_id=user.id,
        responsible_user_id=user.id,
        title=event_title,
        event_type="evento",
        starts_at=datetime.now(UTC) + timedelta(days=1),
    )
    await SqlAlchemyEventRepository(session).save(event)

    await session.commit()
    return tenant.id, event.id


async def test_rls_blocks_cross_tenant_event_select(db_session: AsyncSession) -> None:
    tenant_a_id, event_a_id = await _create_tenant_user_and_event(
        db_session,
        tenant_name="RLS Events Tenant A",
        email=f"rls-event-a-{uuid.uuid4().hex[:8]}@teste.dev",
        event_title="Evento A",
    )
    _tenant_b_id, event_b_id = await _create_tenant_user_and_event(
        db_session,
        tenant_name="RLS Events Tenant B",
        email=f"rls-event-b-{uuid.uuid4().hex[:8]}@teste.dev",
        event_title="Evento B",
    )

    await set_tenant_context(db_session, tenant_a_id)
    result = await db_session.execute(text("SELECT id, tenant_id FROM events"))
    rows = result.fetchall()

    visible_ids = {row.id for row in rows}
    assert event_a_id in visible_ids
    assert event_b_id not in visible_ids, "VAZAMENTO: evento de outro tenant apareceu numa query sem filtro"
    assert all(row.tenant_id == tenant_a_id for row in rows)


async def test_rls_blocks_event_select_when_no_tenant_context_is_set(db_session: AsyncSession) -> None:
    await _create_tenant_user_and_event(
        db_session,
        tenant_name="RLS Events Sem Contexto",
        email=f"rls-event-nc-{uuid.uuid4().hex[:8]}@teste.dev",
        event_title="Evento Sem Contexto",
    )

    result = await db_session.execute(text("SELECT id FROM events"))
    assert result.fetchall() == [], "sem contexto de tenant, deveria retornar zero linhas (fail-closed)"


async def test_rls_blocks_event_insert_with_mismatched_tenant_id(db_session: AsyncSession) -> None:
    tenant_a_id, _ = await _create_tenant_user_and_event(
        db_session,
        tenant_name="RLS Events Insert A",
        email=f"rls-event-insert-a-{uuid.uuid4().hex[:8]}@teste.dev",
        event_title="Evento Insert A",
    )

    fake_other_tenant_id = uuid.uuid4()
    await set_tenant_context(db_session, tenant_a_id)

    with pytest.raises(DBAPIError):
        await db_session.execute(
            text(
                """
                INSERT INTO events
                    (id, tenant_id, created_by_user_id, responsible_user_id, title, event_type, status, starts_at)
                VALUES
                    (:id, :tenant_id, :user_id, :user_id, 'Invasor', 'evento', 'agendado', now())
                """
            ),
            {"id": uuid.uuid4(), "tenant_id": fake_other_tenant_id, "user_id": uuid.uuid4()},
        )
