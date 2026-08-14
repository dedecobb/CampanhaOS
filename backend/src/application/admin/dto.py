from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AdminLoginInput:
    email: str
    password: str


@dataclass(frozen=True)
class AdminLoginOutput:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class AdminRefreshTokenInput:
    refresh_token: str


@dataclass(frozen=True)
class AdminRefreshTokenOutput:
    access_token: str
    refresh_token: str


@dataclass(frozen=True)
class ListTenantsInput:
    search_text: str | None = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class GetTenantInput:
    tenant_id: UUID


@dataclass(frozen=True)
class SuspendTenantInput:
    tenant_id: UUID


@dataclass(frozen=True)
class ActivateTenantInput:
    tenant_id: UUID


@dataclass(frozen=True)
class TenantAdminOutput:
    id: UUID
    name: str
    status: str
    created_at: datetime


@dataclass(frozen=True)
class ListTenantsOutput:
    items: list[TenantAdminOutput]
    total: int
    page: int
    page_size: int
    total_pages: int