"""
Implementação concreta de PlatformAdminRepository usando SQLAlchemy async.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.admin.entities import PlatformAdmin
from src.domain.admin.repository import PlatformAdminRepository
from src.domain.users.value_objects import Email
from src.infrastructure.database.models import PlatformAdminModel


class SqlAlchemyPlatformAdminRepository(PlatformAdminRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, admin: PlatformAdmin) -> None:
        existing = await self._session.get(PlatformAdminModel, admin.id)
        if existing is None:
            model = PlatformAdminModel(
                id=admin.id,
                name=admin.name,
                email=str(admin.email),
                password_hash=admin.password_hash,
                is_active=admin.is_active,
            )
            self._session.add(model)
        else:
            existing.name = admin.name
            existing.is_active = admin.is_active
            # e-mail e password_hash têm fluxos próprios de troca (mesmo
            # padrão já estabelecido em UserRepository, Módulo 1) — não
            # editáveis via este save genérico.

        await self._session.flush()

    async def find_by_id(self, admin_id: UUID) -> PlatformAdmin | None:
        model = await self._session.get(PlatformAdminModel, admin_id)
        return self._to_domain(model) if model else None

    async def find_by_email(self, email: Email) -> PlatformAdmin | None:
        stmt = select(PlatformAdminModel).where(PlatformAdminModel.email == str(email))
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def _to_domain(self, model: PlatformAdminModel) -> PlatformAdmin:
        return PlatformAdmin(
            id=model.id,
            name=model.name,
            email=Email(model.email),
            password_hash=model.password_hash,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
