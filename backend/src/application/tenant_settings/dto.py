from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GenerateRegistrationTokenInput:
    tenant_id: UUID


@dataclass(frozen=True)
class RevokeRegistrationTokenInput:
    tenant_id: UUID


@dataclass(frozen=True)
class GetRegistrationTokenInput:
    tenant_id: UUID


@dataclass(frozen=True)
class RegistrationTokenOutput:
    token: str | None
