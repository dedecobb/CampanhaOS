"""
Portas de segurança usadas pelos casos de uso de autenticação.

Assim como os repositórios (domain/*/repository.py), estas são interfaces
abstratas — a implementação real (bcrypt via passlib, JWT via python-jose,
blocklist via Redis) vive na camada de infraestrutura (Bloco D) e é
injetada nos casos de uso. Isso permite testar login/registro/refresh sem
nenhuma biblioteca de criptografia ou Redis reais.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from src.domain.users.entities import User


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class AccessTokenPayload:
    user_id: UUID
    tenant_id: UUID
    role_names: list[str]


@dataclass(frozen=True)
class RefreshTokenPayload:
    user_id: UUID
    tenant_id: UUID
    jti: str  # "JWT ID": identificador único do token, usado para revogação individual


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, plain_password: str) -> str: ...

    @abstractmethod
    def verify(self, plain_password: str, password_hash: str) -> bool: ...


class TokenService(ABC):
    @abstractmethod
    def create_token_pair(self, user: User) -> TokenPair: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> AccessTokenPayload:
        """Deve levantar `InvalidTokenError` (application/auth/exceptions.py) se inválido/expirado."""

    @abstractmethod
    def decode_refresh_token(self, token: str) -> RefreshTokenPayload:
        """Deve levantar `InvalidTokenError` se inválido/expirado."""


class RefreshTokenBlocklist(ABC):
    """
    Port sobre o mecanismo de revogação de refresh tokens (Redis, no
    Bloco D). Existe separado de TokenService porque validar a ASSINATURA
    de um token (TokenService) e checar se ele foi REVOGADO (esta porta)
    são preocupações diferentes — a primeira é criptografia pura, a
    segunda é estado mutável.
    """

    @abstractmethod
    async def revoke(self, jti: str, ttl_seconds: int) -> None: ...

    @abstractmethod
    async def is_revoked(self, jti: str) -> bool: ...


class TenantContextSetter(ABC):
    """
    Port que avisa a camada de persistência qual tenant está ativo na
    transação atual — necessário porque `users`/`roles` têm Row-Level
    Security (ADR-002) e algumas operações precisam declarar o tenant
    ANTES de existir qualquer autenticação prévia (registro de tenant,
    login, refresh token). A implementação real (Bloco E) apenas chama
    `set_tenant_context` (Bloco B) na sessão SQLAlchemy da requisição.

    O caso de uso não sabe (nem deveria saber) que isso é RLS/PostgreSQL
    por baixo — do ponto de vista dele, é só "declarar qual tenant está
    sendo operado agora".
    """

    @abstractmethod
    async def set_context(self, tenant_id: UUID) -> None: ...
