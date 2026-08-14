"""
Testes de isolamento de tenant no nível de banco (RLS) para `leaderships`.

Mesmo padrão de test_tenant_isolation.py e test_voter_tenant_isolation.py.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.leaderships.entities import Leadership
from src.domain.tenants.entities import Tenant
from src.domain.users.entities import User
from src.domain.users.value_objects import Email
from src.infrastructure.database.repositories.leadership_repository import SqlAlchemyLeadershipRepository
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.database.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.database.session import set_tenant_context
from src.infrastructure.security.password_hasher import BcryptPasswordHasher


async def _create_tenant_user_and_leadership(
    session: AsyncSession, *, tenant_name: str, email: str, leadership_name: str
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

    leadership = Leadership.create(
        tenant_id=tenant.id,
        created_by_user_id=user.id,
        name=leadership_name,
        influence_level="alta",
    )
    await SqlAlchemyLeadershipRepository(session).save(leadership)

    await session.commit()
    return tenant.id, leadership.id


async def test_rls_blocks_cross_tenant_leadership_select(db_session: AsyncSession) -> None:
    tenant_a_id, leadership_a_id = await _create_tenant_user_and_leadership(
        db_session,
        tenant_name="RLS Leaderships Tenant A",
        email=f"rls-lead-a-{uuid.uuid4().hex[:8]}@teste.dev",
        leadership_name="Liderança A",
    )
    _tenant_b_id, leadership_b_id = await _create_tenant_user_and_leadership(
        db_session,
        tenant_name="RLS Leaderships Tenant B",
        email=f"rls-lead-b-{uuid.uuid4().hex[:8]}@teste.dev",
        leadership_name="Liderança B",
    )

    await set_tenant_context(db_session, tenant_a_id)
    result = await db_session.execute(text("SELECT id, tenant_id FROM leaderships"))
    rows = result.fetchall()

    visible_ids = {row.id for row in rows}
    assert leadership_a_id in visible_ids
    assert leadership_b_id not in visible_ids, "VAZAMENTO: liderança de outro tenant apareceu numa query sem filtro"
    assert all(row.tenant_id == tenant_a_id for row in rows)


async def test_rls_blocks_leadership_select_when_no_tenant_context_is_set(db_session: AsyncSession) -> None:
    await _create_tenant_user_and_leadership(
        db_session,
        tenant_name="RLS Leaderships Sem Contexto",
        email=f"rls-lead-nc-{uuid.uuid4().hex[:8]}@teste.dev",
        leadership_name="Liderança Sem Contexto",
    )

    result = await db_session.execute(text("SELECT id FROM leaderships"))
    assert result.fetchall() == [], "sem contexto de tenant, deveria retornar zero linhas (fail-closed)"


async def test_rls_blocks_leadership_insert_with_mismatched_tenant_id(db_session: AsyncSession) -> None:
    tenant_a_id, _ = await _create_tenant_user_and_leadership(
        db_session,
        tenant_name="RLS Leaderships Insert A",
        email=f"rls-lead-insert-a-{uuid.uuid4().hex[:8]}@teste.dev",
        leadership_name="Liderança Insert A",
    )

    fake_other_tenant_id = uuid.uuid4()
    await set_tenant_context(db_session, tenant_a_id)

    with pytest.raises(DBAPIError):
        await db_session.execute(
            text(
                """
                INSERT INTO leaderships (id, tenant_id, created_by_user_id, name, influence_level, estimated_votes)
                VALUES (:id, :tenant_id, :user_id, 'Invasor', 'alta', 0)
                """
            ),
            {"id": uuid.uuid4(), "tenant_id": fake_other_tenant_id, "user_id": uuid.uuid4()},
        )
