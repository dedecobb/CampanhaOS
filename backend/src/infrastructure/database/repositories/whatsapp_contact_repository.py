"""
Implementação concreta de WhatsAppContactRepository usando SQLAlchemy async.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.whatsapp.entities import WhatsAppContact
from src.domain.whatsapp.repository import WhatsAppContactRepository
from src.infrastructure.database.models import WhatsAppContactModel


class SqlAlchemyWhatsAppContactRepository(WhatsAppContactRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, contact: WhatsAppContact) -> None:
        existing = await self._session.get(WhatsAppContactModel, contact.id)
        if existing is None:
            model = WhatsAppContactModel(
                id=contact.id,
                tenant_id=contact.tenant_id,
                phone_number=contact.phone_number,
                voter_id=contact.voter_id,
                opted_in_at=contact.opted_in_at,
                opt_in_source=contact.opt_in_source,
                opted_out_at=contact.opted_out_at,
            )
            self._session.add(model)
        else:
            existing.voter_id = contact.voter_id
            existing.opted_in_at = contact.opted_in_at
            existing.opted_out_at = contact.opted_out_at

        await self._session.flush()

    async def find_by_id(self, tenant_id: UUID, contact_id: UUID) -> WhatsAppContact | None:
        stmt = select(WhatsAppContactModel).where(
            WhatsAppContactModel.tenant_id == tenant_id,
            WhatsAppContactModel.id == contact_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_phone_number(self, tenant_id: UUID, phone_number: str) -> WhatsAppContact | None:
        stmt = select(WhatsAppContactModel).where(
            WhatsAppContactModel.tenant_id == tenant_id,
            WhatsAppContactModel.phone_number == phone_number,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def list_opted_in(self, tenant_id: UUID) -> list[WhatsAppContact]:
        stmt = select(WhatsAppContactModel).where(
            WhatsAppContactModel.tenant_id == tenant_id,
            WhatsAppContactModel.opted_out_at.is_(None),
        )
        models = (await self._session.execute(stmt)).scalars().all()
        return [self._to_domain(m) for m in models]

    def _to_domain(self, model: WhatsAppContactModel) -> WhatsAppContact:
        return WhatsAppContact(
            id=model.id,
            tenant_id=model.tenant_id,
            phone_number=model.phone_number,
            voter_id=model.voter_id,
            opted_in_at=model.opted_in_at,
            opt_in_source=model.opt_in_source,
            opted_out_at=model.opted_out_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
