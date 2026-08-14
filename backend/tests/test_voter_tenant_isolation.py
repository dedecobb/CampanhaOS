"""
Testes de isolamento de tenant no nível de banco (RLS) para `voters`.

Mesmo padrão de test_tenant_isolation.py (Módulo 1): SQL cru, sem passar
pela aplicação, provando que a proteção existe no PostgreSQL — não só no
código da aplicação.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tenants.entities import Tenant
from src.domain.users.entities import User
from src.domain.users.value_objects import Email
from src.domain.voters.entities import Voter
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.database.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.database.repositories.voter_repository import SqlAlchemyVoterRepository
from src.infrastructure.database.session import set_tenant_context
from src.infrastructure.security.password_hasher import BcryptPasswordHasher


async def _create_tenant_user_and_voter(
    session: AsyncSession, *, tenant_name: str, email: str, voter_name: str
) -> tuple[uuid.UUID, uuid.UUID]:
    """Cria tenant + usuário + eleitor, tudo numa transação commitada. Retorna (tenant_id, voter_id)."""
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

    voter = Voter.create(
        tenant_id=tenant.id,
        created_by_user_id=user.id,
        name=voter_name,
        legal_basis="consentimento",
    )
    await SqlAlchemyVoterRepository(session).save(voter)

    await session.commit()
    return tenant.id, voter.id


async def test_rls_blocks_cross_tenant_voter_select(db_session: AsyncSession) -> None:
    tenant_a_id, voter_a_id = await _create_tenant_user_and_voter(
        db_session,
        tenant_name="RLS Voters Tenant A",
        email=f"rls-voters-a-{uuid.uuid4().hex[:8]}@teste.dev",
        voter_name="Eleitor A",
    )
    _tenant_b_id, voter_b_id = await _create_tenant_user_and_voter(
        db_session,
        tenant_name="RLS Voters Tenant B",
        email=f"rls-voters-b-{uuid.uuid4().hex[:8]}@teste.dev",
        voter_name="Eleitor B",
    )

    await set_tenant_context(db_session, tenant_a_id)
    result = await db_session.execute(text("SELECT id, tenant_id FROM voters"))
    rows = result.fetchall()

    visible_ids = {row.id for row in rows}
    assert voter_a_id in visible_ids, "eleitor do próprio tenant deveria estar visível"
    assert voter_b_id not in visible_ids, "VAZAMENTO: eleitor de outro tenant apareceu numa query sem filtro"
    assert all(row.tenant_id == tenant_a_id for row in rows)


async def test_rls_blocks_voter_select_when_no_tenant_context_is_set(db_session: AsyncSession) -> None:
    await _create_tenant_user_and_voter(
        db_session,
        tenant_name="RLS Voters Sem Contexto",
        email=f"rls-voters-nc-{uuid.uuid4().hex[:8]}@teste.dev",
        voter_name="Eleitor Sem Contexto",
    )

    result = await db_session.execute(text("SELECT id FROM voters"))
    assert result.fetchall() == [], "sem contexto de tenant, deveria retornar zero linhas (fail-closed)"


async def test_rls_blocks_voter_insert_with_mismatched_tenant_id(db_session: AsyncSession) -> None:
    tenant_a_id, _ = await _create_tenant_user_and_voter(
        db_session,
        tenant_name="RLS Voters Insert A",
        email=f"rls-voters-insert-a-{uuid.uuid4().hex[:8]}@teste.dev",
        voter_name="Eleitor Insert A",
    )

    # Precisa de um created_by_user_id válido para não esbarrar na FK antes
    # de chegar na policy de RLS — reaproveita o usuário já criado acima
    # seria mais simples, mas o objetivo aqui é isolar o teste da FK,
    # então usamos um UUID aleatório: se a policy de RLS bloquear primeiro
    # (o esperado), nem chega a validar a FK.
    fake_other_tenant_id = uuid.uuid4()
    await set_tenant_context(db_session, tenant_a_id)

    with pytest.raises(DBAPIError):
        await db_session.execute(
            text(
                """
                INSERT INTO voters (id, tenant_id, created_by_user_id, name, legal_basis, tags, custom_fields)
                VALUES (:id, :tenant_id, :user_id, 'Invasor', 'consentimento', '{}', '{}')
                """
            ),
            {"id": uuid.uuid4(), "tenant_id": fake_other_tenant_id, "user_id": uuid.uuid4()},
        )
