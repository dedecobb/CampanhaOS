"""
Testes de isolamento de tenant no nível de banco (RLS) para
`finance_transactions`, e da CHECK constraint de valor positivo.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.finance.entities import FinanceTransaction
from src.domain.tenants.entities import Tenant
from src.domain.users.entities import User
from src.domain.users.value_objects import Email
from src.infrastructure.database.repositories.finance_repository import SqlAlchemyFinanceRepository
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.database.repositories.user_repository import SqlAlchemyUserRepository
from src.infrastructure.database.session import set_tenant_context
from src.infrastructure.security.password_hasher import BcryptPasswordHasher


async def _create_tenant_user_and_transaction(
    session: AsyncSession, *, tenant_name: str, email: str, category: str
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    """Retorna (tenant_id, transaction_id, user_id) — o user_id é exposto
    para testes que precisam de uma FK válida sem ambiguidade (ver
    test_check_constraint_blocks_non_positive_amount)."""
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

    transaction = FinanceTransaction.create(
        tenant_id=tenant.id,
        created_by_user_id=user.id,
        type="receita",
        category=category,
        amount=Decimal("100.00"),
        occurred_at=date.today(),
    )
    await SqlAlchemyFinanceRepository(session).save(transaction)

    await session.commit()
    return tenant.id, transaction.id, user.id


async def test_rls_blocks_cross_tenant_finance_select(db_session: AsyncSession) -> None:
    tenant_a_id, transaction_a_id, _user_a_id = await _create_tenant_user_and_transaction(
        db_session,
        tenant_name="RLS Finance Tenant A",
        email=f"rls-finance-a-{uuid.uuid4().hex[:8]}@teste.dev",
        category="Categoria A",
    )
    _tenant_b_id, transaction_b_id, _user_b_id = await _create_tenant_user_and_transaction(
        db_session,
        tenant_name="RLS Finance Tenant B",
        email=f"rls-finance-b-{uuid.uuid4().hex[:8]}@teste.dev",
        category="Categoria B",
    )

    await set_tenant_context(db_session, tenant_a_id)
    result = await db_session.execute(text("SELECT id, tenant_id FROM finance_transactions"))
    rows = result.fetchall()

    visible_ids = {row.id for row in rows}
    assert transaction_a_id in visible_ids
    assert transaction_b_id not in visible_ids, "VAZAMENTO: lançamento de outro tenant apareceu numa query sem filtro"
    assert all(row.tenant_id == tenant_a_id for row in rows)


async def test_rls_blocks_finance_select_when_no_tenant_context_is_set(db_session: AsyncSession) -> None:
    await _create_tenant_user_and_transaction(
        db_session,
        tenant_name="RLS Finance Sem Contexto",
        email=f"rls-finance-nc-{uuid.uuid4().hex[:8]}@teste.dev",
        category="Categoria",
    )
    result = await db_session.execute(text("SELECT id FROM finance_transactions"))
    assert result.fetchall() == [], "sem contexto de tenant, deveria retornar zero linhas (fail-closed)"


async def test_rls_blocks_finance_insert_with_mismatched_tenant_id(db_session: AsyncSession) -> None:
    tenant_a_id, _transaction_id, _user_id = await _create_tenant_user_and_transaction(
        db_session,
        tenant_name="RLS Finance Insert A",
        email=f"rls-finance-insert-a-{uuid.uuid4().hex[:8]}@teste.dev",
        category="Categoria",
    )

    fake_other_tenant_id = uuid.uuid4()
    await set_tenant_context(db_session, tenant_a_id)

    with pytest.raises(DBAPIError):
        await db_session.execute(
            text(
                """
                INSERT INTO finance_transactions
                    (id, tenant_id, created_by_user_id, type, category, amount, occurred_at)
                VALUES
                    (:id, :tenant_id, :user_id, 'receita', 'Invasor', 100.00, CURRENT_DATE)
                """
            ),
            {"id": uuid.uuid4(), "tenant_id": fake_other_tenant_id, "user_id": uuid.uuid4()},
        )


async def test_check_constraint_blocks_non_positive_amount(db_session: AsyncSession) -> None:
    """
    Prova a SEGUNDA camada de defesa do Bloco B: mesmo pulando o domínio
    inteiro (SQL cru direto na tabela, dentro do próprio tenant, sem
    nenhuma violação de RLS), a CHECK constraint do banco ainda rejeita
    um valor zero ou negativo.
    """
    tenant_a_id, _transaction_id, user_a_id = await _create_tenant_user_and_transaction(
        db_session,
        tenant_name="RLS Finance Check Constraint",
        email=f"rls-finance-check-{uuid.uuid4().hex[:8]}@teste.dev",
        category="Categoria",
    )

    await set_tenant_context(db_session, tenant_a_id)

    with pytest.raises(DBAPIError):
        await db_session.execute(
            text(
                """
                INSERT INTO finance_transactions
                    (id, tenant_id, created_by_user_id, type, category, amount, occurred_at)
                VALUES
                    (:id, :tenant_id, :user_id, 'despesa', 'Valor inválido', -50.00, CURRENT_DATE)
                """
            ),
            {"id": uuid.uuid4(), "tenant_id": tenant_a_id, "user_id": user_a_id},
        )
