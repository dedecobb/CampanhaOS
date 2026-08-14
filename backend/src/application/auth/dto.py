"""
DTOs (Data Transfer Objects) dos casos de uso de autenticação.

Por que DTOs próprios em vez de reusar os schemas Pydantic da API
(Bloco E): a camada de aplicação não deve depender de Pydantic/FastAPI —
só a camada de presentation depende deles. Os schemas Pydantic do Bloco E
vão converter para estes DTOs antes de chamar o caso de uso.
"""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RegisterTenantInput:
    tenant_name: str
    admin_name: str
    admin_email: str
    admin_password: str


@dataclass(frozen=True)
class RegisterTenantOutput:
    tenant_id: UUID
    user_id: UUID


@dataclass(frozen=True)
class LoginInput:
    tenant_id: UUID
    email: str
    password: str


@dataclass(frozen=True)
class LoginOutput:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class RefreshTokenInput:
    refresh_token: str


@dataclass(frozen=True)
class RefreshTokenOutput:
    access_token: str
    refresh_token: str
