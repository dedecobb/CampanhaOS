"""
Implementação concreta de TenantContextSetter (porta definida em
application/auth/ports.py).

É apenas uma fina camada em cima de `set_tenant_context`, já criado no
Bloco B — a existência desta classe separada é o que permite ao caso de
uso depender de uma abstração (`TenantContextSetter`) em vez de conhecer
SQLAlchemy ou o mecanismo de RLS diretamente.
"""

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth.ports import TenantContextSetter
from src.infrastructure.database.session import set_tenant_context


class SqlAlchemyTenantContextSetter(TenantContextSetter):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def set_context(self, tenant_id: UUID) -> None:
        await set_tenant_context(self._session, tenant_id)
