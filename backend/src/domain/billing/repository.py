"""
Portas (interfaces) dos repositórios de Plan e Subscription.
"""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.billing.entities import Plan, Subscription


class PlanRepository(ABC):
    @abstractmethod
    async def save(self, plan: Plan) -> None:
        """Persiste um plano novo ou atualiza um existente (upsert por id). Não escopado a tenant — catálogo global."""

    @abstractmethod
    async def find_by_id(self, plan_id: UUID) -> Plan | None:
        pass

    @abstractmethod
    async def exists_active(self, plan_id: UUID) -> bool:
        """Usado para validar que um plano existe e está ativo antes de associá-lo a uma assinatura."""

    @abstractmethod
    async def list_all(self, *, only_active: bool = False) -> list[Plan]:
        """
        Sem paginação de propósito: o catálogo de planos é pequeno por
        natureza (dezenas, não milhares) — paginar aqui seria complexidade
        sem benefício real.
        """


class SubscriptionRepository(ABC):
    @abstractmethod
    async def save(self, subscription: Subscription) -> None:
        """Persiste. Escopado a tenant (RLS) — diferente de PlanRepository."""

    @abstractmethod
    async def find_by_tenant_id(self, tenant_id: UUID) -> Subscription | None:
        """
        Busca a assinatura de UM tenant específico. Sob a decisão de
        escopo deste módulo (sem bypass de RLS), o chamador (caso de uso
        de super-admin) precisa ter declarado o contexto daquele tenant
        antes de chamar este método — mesmo mecanismo que qualquer outro
        acesso tenant-scoped no projeto.
        """
