"""
Entidade de domínio: Tenant.

Um Tenant representa uma campanha eleitoral cadastrada no SaaS. É a
unidade de isolamento de todo o sistema (ADR-002 do documento fonte da
verdade) — toda tabela de negócio criada a partir do Módulo 2 em diante
vai carregar uma referência a um Tenant.

Esta classe NÃO sabe como é persistida (não conhece SQLAlchemy, não
conhece PostgreSQL). Ela só sabe as regras que fazem um Tenant ser um
Tenant válido.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from src.domain.shared.exceptions import InvalidNameError


class TenantStatus(str, Enum):
    """
    Ciclo de vida de um tenant.

    TRIAL: período de teste, sem cobrança ainda (usado a partir do Módulo 7 - Billing).
    ACTIVE: assinatura ativa, uso normal do sistema.
    SUSPENDED: inadimplente ou suspenso manualmente pelo super-admin — usuários
               do tenant não devem conseguir logar enquanto SUSPENDED.
    CANCELLED: encerrado. Dado é retido conforme política de retenção (a
               definir no módulo de Billing/LGPD), mas o tenant não opera mais.
    """

    TRIAL = "trial"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"


@dataclass
class Tenant:
    id: UUID
    name: str
    status: TenantStatus
    created_at: datetime

    @staticmethod
    def create(name: str) -> "Tenant":
        """
        Factory method para criar um novo Tenant.

        Usamos um método de fábrica em vez de deixar o `__init__` livre
        porque a CRIAÇÃO de um tenant tem regras próprias (gerar id, definir
        status inicial, timestamp) que não fazem sentido serem repetidas
        toda vez que reconstruímos um Tenant a partir do banco de dados
        (nesse segundo caso, usamos o `__init__`/construtor normal do
        dataclass diretamente, via o repository).
        """
        Tenant._validate_name(name)
        return Tenant(
            id=uuid4(),
            name=name.strip(),
            status=TenantStatus.TRIAL,
            created_at=datetime.now(UTC),
        )

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise InvalidNameError("Nome do tenant não pode ser vazio")
        if len(name.strip()) < 3:
            raise InvalidNameError("Nome do tenant precisa ter ao menos 3 caracteres")

    def suspend(self) -> None:
        """Regra de negócio: só é possível suspender um tenant ativo ou em trial."""
        if self.status == TenantStatus.CANCELLED:
            raise InvalidNameError("Não é possível suspender um tenant já cancelado")
        self.status = TenantStatus.SUSPENDED

    def activate(self) -> None:
        if self.status == TenantStatus.CANCELLED:
            raise InvalidNameError("Não é possível reativar um tenant cancelado")
        self.status = TenantStatus.ACTIVE

    @property
    def can_authenticate(self) -> bool:
        """
        Regra de negócio central: apenas tenants TRIAL ou ACTIVE permitem
        login de usuários. Usado pelo caso de uso de login no Bloco C.
        """
        return self.status in (TenantStatus.TRIAL, TenantStatus.ACTIVE)
