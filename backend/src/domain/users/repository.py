"""
Porta (interface) do repositório de User.

Este é o mecanismo central do padrão Ports & Adapters (Hexagonal): o
domínio define O QUE precisa ser possível fazer com um User em termos de
persistência ("buscar por e-mail dentro de um tenant", "salvar"), mas NÃO
COMO isso é feito. A implementação concreta (Bloco B, usando SQLAlchemy +
PostgreSQL) vive em `infrastructure/database/repositories/`.

Por que isso importa na prática: os casos de uso (Bloco C) vão depender
desta interface, nunca da implementação concreta. Isso permite, por
exemplo, testar um caso de uso de login com um repositório "fake" em
memória, sem precisar de PostgreSQL rodando — testes de aplicação ficam
rápidos e não-frágeis.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.users.entities import User
from src.domain.users.value_objects import Email


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> None:
        """Persiste um usuário novo ou atualiza um existente (upsert por id)."""

    @abstractmethod
    async def find_by_id(self, tenant_id: UUID, user_id: UUID) -> User | None:
        """
        Busca por id SEMPRE escopado a um tenant_id.

        Esta assinatura é proposital: é estruturalmente impossível chamar
        este método sem informar de qual tenant você está buscando — isso é
        uma camada de proteção do RN-01 (isolamento de tenant) já no nível
        da interface, antes mesmo de qualquer RLS no banco.
        """

    @abstractmethod
    async def find_by_email(self, tenant_id: UUID, email: Email) -> User | None:
        """
        Busca por e-mail, escopado a um tenant.

        Nota de regra de negócio: o mesmo e-mail PODE existir em tenants
        diferentes (ex: a mesma pessoa trabalhando em duas campanhas
        distintas) — por isso a unicidade de e-mail é por (tenant_id, email),
        nunca global. Essa regra será refletida na constraint do banco no
        Bloco B.
        """

    @abstractmethod
    async def email_exists(self, tenant_id: UUID, email: Email) -> bool:
        """Usado na validação de cadastro, antes de tentar salvar."""
