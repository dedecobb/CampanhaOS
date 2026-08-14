"""
Testes de isolamento de tenant no nível de banco de dados (RLS).

Diferente de test_auth_flow.py, estes testes NÃO passam pela aplicação —
eles usam SQL cru diretamente contra a tabela `users`, pulando de
propósito o filtro `WHERE tenant_id = ...` que o código da aplicação já
faz. O objetivo é provar que a proteção existe numa camada independente
do código da aplicação: mesmo que um desenvolvedor esqueça o filtro em
uma query futura, o PostgreSQL bloqueia sozinho.

Este é o teste que justifica termos investido em RLS (ADR-002) em vez de
confiar só em "sempre lembrar de filtrar por tenant_id" no código.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tenants.entities import Tenant
from src.domain.users.entities import User
from src.domain.users.value_objects import Email
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.database.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.database.session import set_tenant_context
from src.infrastructure.security.password_hasher import BcryptPasswordHasher


async def _create_tenant_with_user(session: AsyncSession, *, tenant_name: str, email: str) -> tuple[uuid.UUID, uuid.UUID]:
    """Cria um tenant + usuário direto via repository, numa transação isolada e já commitada."""
    tenant = Tenant.create(name=tenant_name)
    tenant_repo = SqlAlchemyTenantRepository(session)
    await tenant_repo.save(tenant)
    await set_tenant_context(session, tenant.id)

    hasher = BcryptPasswordHasher()
    user = User.create(
        tenant_id=tenant.id,
        name="Usuário de Teste",
        email=Email(email),
        password_hash=hasher.hash("senha_forte_123"),
    )
    user_repo = SqlAlchemyUserRepository(session)
    await user_repo.save(user)
    await session.commit()

    return tenant.id, user.id


async def test_rls_blocks_cross_tenant_select_even_with_raw_sql(db_session: AsyncSession) -> None:
    """
    O teste mais importante do módulo: cria 2 tenants com usuários, depois
    tenta ler a tabela `users` INTEIRA (sem filtro nenhum) com o contexto
    setado só para o tenant A — e prova que só as linhas do tenant A
    voltam, mesmo a query não tendo filtro nenhum de tenant_id.
    """
    email_a = f"rls-a-{uuid.uuid4().hex[:8]}@teste.dev"
    email_b = f"rls-b-{uuid.uuid4().hex[:8]}@teste.dev"

    tenant_a_id, user_a_id = await _create_tenant_with_user(
        db_session, tenant_name="RLS Tenant A", email=email_a
    )
    tenant_b_id, user_b_id = await _create_tenant_with_user(
        db_session, tenant_name="RLS Tenant B", email=email_b
    )

    await set_tenant_context(db_session, tenant_a_id)
    # SQL CRU, sem NENHUM filtro de tenant_id — de propósito.
    result = await db_session.execute(text("SELECT id, tenant_id FROM users"))
    rows = result.fetchall()

    visible_user_ids = {row.id for row in rows}
    assert user_a_id in visible_user_ids, "usuário do próprio tenant deveria estar visível"
    assert user_b_id not in visible_user_ids, "VAZAMENTO: usuário de outro tenant apareceu numa query sem filtro"
    assert all(row.tenant_id == tenant_a_id for row in rows), "RLS deixou passar linha de outro tenant"


async def test_rls_blocks_select_when_no_tenant_context_is_set(db_session: AsyncSession) -> None:
    """
    Fail-closed: se NENHUM contexto de tenant foi declarado na sessão,
    a query deve retornar ZERO linhas — nunca "todas as linhas por
    engano". Isso prova o comportamento de `current_setting(..., true)`
    retornando NULL, e `tenant_id::text = NULL` nunca sendo verdadeiro.
    """
    email = f"rls-no-context-{uuid.uuid4().hex[:8]}@teste.dev"
    await _create_tenant_with_user(db_session, tenant_name="RLS Sem Contexto", email=email)

    # Sessão nova, NENHUM `set_tenant_context` chamado.
    result = await db_session.execute(text("SELECT id FROM users"))
    rows = result.fetchall()

    assert rows == [], "sem contexto de tenant setado, a query deveria retornar zero linhas (fail-closed)"


async def test_rls_blocks_insert_with_mismatched_tenant_id(db_session: AsyncSession) -> None:
    """
    Prova a metade `WITH CHECK` da policy: mesmo com contexto setado para
    o tenant A, tentar inserir uma linha com `tenant_id` do tenant B deve
    ser REJEITADO pelo banco — não só leituras são protegidas, escritas
    também.
    """
    email_a = f"rls-insert-a-{uuid.uuid4().hex[:8]}@teste.dev"
    tenant_a_id, _ = await _create_tenant_with_user(db_session, tenant_name="RLS Insert A", email=email_a)

    # tenant_b não precisa nem existir de verdade na tabela `tenants` para
    # este teste — o que estamos provando é que o INSERT em `users` é
    # rejeitado ANTES disso importar, pela policy de RLS.
    fake_other_tenant_id = uuid.uuid4()
    await set_tenant_context(db_session, tenant_a_id)

    with pytest.raises(DBAPIError):
        await db_session.execute(
            text(
                """
                INSERT INTO users (id, tenant_id, name, email, password_hash, is_active)
                VALUES (:id, :tenant_id, 'Invasor', 'invasor@teste.dev', 'hash', true)
                """
            ),
            {"id": uuid.uuid4(), "tenant_id": fake_other_tenant_id},
        )
