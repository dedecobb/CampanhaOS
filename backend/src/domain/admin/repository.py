"""
Porta (interface) do repositório de PlatformAdmin.

Sem escopo de tenant (não faz sentido — PlatformAdmin não pertence a
nenhum), diferente de todo outro repository do projeto até agora.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.admin.entities import PlatformAdmin
from src.domain.users.value_objects import Email


class PlatformAdminRepository(ABC):
    @abstractmethod
    async def save(self, admin: PlatformAdmin) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, admin_id: UUID) -> PlatformAdmin | None:
        pass

    @abstractmethod
    async def find_by_email(self, email: Email) -> PlatformAdmin | None:
        """
        Diferente de `UserRepository.find_by_email` (Módulo 1), aqui a
        busca é GLOBAL — e-mail de super-admin é único na plataforma
        inteira, não por tenant (não existe "tenant" pra um super-admin).
        """
