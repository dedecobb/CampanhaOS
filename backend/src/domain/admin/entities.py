"""
Entidade de domínio: PlatformAdmin.

Deliberadamente SEPARADA de `User` (Módulo 1) — um super-admin não
pertence a nenhum tenant, então não faz sentido ele "morar" na tabela
`users` (que é conceitualmente "gente de uma campanha", com RLS). Reusa o
Value Object `Email` do domínio de usuários (mesma regra de formato,
não faz sentido duplicar).
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.shared.exceptions import InvalidNameError
from src.domain.users.value_objects import Email


@dataclass
class PlatformAdmin:
    id: UUID
    name: str
    email: Email
    password_hash: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(name: str, email: Email, password_hash: str) -> "PlatformAdmin":
        if not name or not name.strip():
            raise InvalidNameError("Nome do administrador não pode ser vazio")

        now = datetime.now(UTC)
        return PlatformAdmin(
            id=uuid4(),
            name=name.strip(),
            email=email,
            password_hash=password_hash,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    def deactivate(self) -> None:
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        self.is_active = True
        self.updated_at = datetime.now(UTC)
