"""
Portas de autenticação de super-admin.

Deliberadamente SEPARADAS de `application/auth/ports.py` (TokenService,
para usuários de tenant) — reaproveitamos só o `TokenPair` (formato de
saída idêntico: access + refresh), mas o payload do token de admin não
tem `tenant_id`/`role_names`, e a implementação real (Bloco D) vai marcar
o token com um campo distinto (`"type": "platform_admin_access"`), pra um
token de usuário normal nunca poder ser decodificado como token de admin,
mesmo usando a mesma chave secreta.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from uuid import UUID

from src.application.auth.ports import TokenPair
from src.domain.admin.entities import PlatformAdmin


@dataclass(frozen=True)
class PlatformAdminAccessTokenPayload:
    admin_id: UUID


@dataclass(frozen=True)
class PlatformAdminRefreshTokenPayload:
    admin_id: UUID
    jti: str


class PlatformAdminTokenService(ABC):
    @abstractmethod
    def create_token_pair(self, admin: PlatformAdmin) -> TokenPair: ...

    @abstractmethod
    def decode_access_token(self, token: str) -> PlatformAdminAccessTokenPayload:
        """Deve levantar InvalidTokenError se inválido/expirado/de outro tipo (ex: token de usuário normal)."""

    @abstractmethod
    def decode_refresh_token(self, token: str) -> PlatformAdminRefreshTokenPayload:
        """Deve levantar InvalidTokenError se inválido/expirado/de outro tipo."""
