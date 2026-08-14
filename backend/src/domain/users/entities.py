"""
Entidade de domínio: User.

Um User pertence sempre a exatamente um Tenant (RN-01 do documento de
Fase 1: isolamento de tenant). Esta entidade não sabe como a senha é
hasheada (isso é `infrastructure/security/`, um "detalhe" de fora do
domínio) — ela só guarda o hash já pronto e sabe comparar.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.shared.exceptions import InvalidNameError
from src.domain.users.value_objects import Email


@dataclass
class User:
    id: UUID
    tenant_id: UUID
    name: str
    email: Email
    password_hash: str
    is_active: bool
    created_at: datetime
    # Nomes de papéis (ex: "admin", "coordenador") atribuídos a este usuário.
    # Mantido como lista simples na entidade de domínio; a modelagem
    # relacional completa (tabelas Role/Permission/UserRole) vive na
    # camada de infraestrutura (Bloco B) e é convertida para esta forma
    # simplificada ao carregar o usuário via repository.
    role_names: list[str] = field(default_factory=list)

    @staticmethod
    def create(
        tenant_id: UUID,
        name: str,
        email: Email,
        password_hash: str,
    ) -> "User":
        if not name or not name.strip():
            raise InvalidNameError("Nome do usuário não pode ser vazio")

        return User(
            id=uuid4(),
            tenant_id=tenant_id,
            name=name.strip(),
            email=email,
            password_hash=password_hash,
            is_active=True,
            created_at=datetime.now(UTC),
            role_names=[],
        )

    def has_role(self, role_name: str) -> bool:
        return role_name in self.role_names

    def deactivate(self) -> None:
        self.is_active = False

    def activate(self) -> None:
        self.is_active = True
