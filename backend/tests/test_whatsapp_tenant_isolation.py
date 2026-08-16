"""
Testes de isolamento de tenant no nível de banco (RLS) para
`whatsapp_contacts` — mesmo padrão de todos os testes de isolamento
anteriores no projeto.
"""

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.tenants.entities import Tenant
from src.domain.whatsapp.entities import WhatsAppContact
from src.infrastructure.database.repositories.tenant_repository import SqlAlchemyTenantRepository
from src.infrastructure.database.repositories.whatsapp_contact_repository import SqlAlchemyWhatsAppContactRepository
from src.infrastructure.database.session import set_tenant_context


async def _create_tenant_and_contact(
    session: AsyncSession, *, tenant_name: str, phone_number: str
) -> tuple[uuid.UUID, uuid.UUID]:
    tenant = Tenant.create(name=tenant_name)
    await SqlAlchemyTenantRepository(session).save(tenant)
    await set_tenant_context(session, tenant.id)

    contact = WhatsAppContact.create(tenant_id=tenant.id, phone_number=phone_number)
    await SqlAlchemyWhatsAppContactRepository(session).save(contact)

    await session.commit()
    return tenant.id, contact.id


async def test_rls_blocks_cross_tenant_whatsapp_contact_select(db_session: AsyncSession) -> None:
    tenant_a_id, contact_a_id = await _create_tenant_and_contact(
        db_session, tenant_name=f"RLS WhatsApp Tenant A {uuid.uuid4().hex[:8]}", phone_number="+5521999998888"
    )
    _tenant_b_id, contact_b_id = await _create_tenant_and_contact(
        db_session, tenant_name=f"RLS WhatsApp Tenant B {uuid.uuid4().hex[:8]}", phone_number="+5521888887777"
    )

    await set_tenant_context(db_session, tenant_a_id)
    result = await db_session.execute(text("SELECT id, tenant_id FROM whatsapp_contacts"))
    rows = result.fetchall()

    visible_ids = {row.id for row in rows}
    assert contact_a_id in visible_ids
    assert contact_b_id not in visible_ids, "VAZAMENTO: contato de outro tenant apareceu numa query sem filtro"
    assert all(row.tenant_id == tenant_a_id for row in rows)


async def test_rls_blocks_whatsapp_contact_select_when_no_tenant_context_is_set(db_session: AsyncSession) -> None:
    await _create_tenant_and_contact(
        db_session,
        tenant_name=f"RLS WhatsApp Sem Contexto {uuid.uuid4().hex[:8]}",
        phone_number="+5521999997777",
    )

    result = await db_session.execute(text("SELECT id FROM whatsapp_contacts"))
    assert result.fetchall() == [], "sem contexto de tenant, deveria retornar zero linhas (fail-closed)"


async def test_rls_blocks_whatsapp_contact_insert_with_mismatched_tenant_id(db_session: AsyncSession) -> None:
    tenant_a_id, _ = await _create_tenant_and_contact(
        db_session,
        tenant_name=f"RLS WhatsApp Insert A {uuid.uuid4().hex[:8]}",
        phone_number="+5521999996666",
    )

    fake_other_tenant_id = uuid.uuid4()
    await set_tenant_context(db_session, tenant_a_id)

    with pytest.raises(DBAPIError):
        await db_session.execute(
            text(
                """
                INSERT INTO whatsapp_contacts (id, tenant_id, phone_number, opted_in_at, opt_in_source)
                VALUES (:id, :tenant_id, :phone_number, now(), 'contato_iniciou_conversa')
                """
            ),
            {"id": uuid.uuid4(), "tenant_id": fake_other_tenant_id, "phone_number": "+5521999995555"},
        )
