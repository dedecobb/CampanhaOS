"""
Porta (interface) do repositório de WhatsAppContact.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.whatsapp.entities import WhatsAppContact


class WhatsAppContactRepository(ABC):
    @abstractmethod
    async def save(self, contact: WhatsAppContact) -> None:
        """Persiste um contato novo ou atualiza um existente (upsert por id)."""

    @abstractmethod
    async def find_by_id(self, tenant_id: UUID, contact_id: UUID) -> WhatsAppContact | None:
        """Busca por id, escopado ao tenant — usado antes de enviar mensagem, para confirmar opt-in."""

    @abstractmethod
    async def find_by_phone_number(self, tenant_id: UUID, phone_number: str) -> WhatsAppContact | None:
        """
        Busca por telefone — usado pelo webhook para saber se um número
        que acabou de mandar mensagem já é um contato conhecido, ou é a
        primeira vez (precisa criar o opt-in).
        """

    @abstractmethod
    async def list_opted_in(self, tenant_id: UUID) -> list[WhatsAppContact]:
        """Lista só os contatos ATIVOS (não descadastrados) — é a lista que pode receber mensagem."""
