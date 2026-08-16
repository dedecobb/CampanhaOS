"""
Modelos SQLAlchemy (camada de infraestrutura).

Estes NÃO são as entidades de domínio do Bloco A — são a representação
concreta das tabelas no PostgreSQL. O repository (próxima entrega) traduz
entre este mundo (SQLAlchemy) e o mundo do domínio (dataclasses puras).

Convenção de nomenclatura do projeto: classes de modelo terminam em
`Model` (ex: `UserModel`) para nunca serem confundidas, num import, com as
entidades de domínio de mesmo nome conceitual (ex: `User`).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    """
    Mixin de auditoria temporal básica. `server_default=func.now()` roda a
    função NOW() do próprio PostgreSQL na hora do INSERT — preferível a
    gerar o timestamp em Python, porque garante consistência mesmo se
    múltiplas instâncias da aplicação (rodando em servidores/fusos
    diferentes) escreverem no mesmo banco.

    `DateTime(timezone=True)`: mapeia para `timestamptz` do PostgreSQL, não
    `timestamp` puro. Todo datetime no domínio é gerado com
    `datetime.now(UTC)` (timezone-aware) — se a coluna do banco fosse
    "sem fuso" (`timestamp`), qualquer datetime timezone-aware vindo do
    Python seria rejeitado pelo driver `asyncpg` (foi exatamente o Bug
    encontrado no Módulo 2, ao implementar soft delete de eleitores).
    """

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class TenantModel(TimestampMixin, Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="trial")

    users: Mapped[list["UserModel"]] = relationship(back_populates="tenant")
    roles: Mapped[list["RoleModel"]] = relationship(back_populates="tenant")


class UserModel(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # Regra de negócio já registrada no Bloco A: e-mail é único POR
        # TENANT, não globalmente.
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    tenant: Mapped["TenantModel"] = relationship(back_populates="users")
    user_roles: Mapped[list["UserRoleModel"]] = relationship(back_populates="user")


class RoleModel(TimestampMixin, Base):
    """
    Papéis são POR TENANT (ex: cada campanha pode, no futuro, customizar
    seus próprios papéis) — por isso `tenant_id` aqui, diferente de
    `PermissionModel` abaixo, que é global.
    """

    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("tenant_id", "name", name="uq_roles_tenant_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    tenant: Mapped["TenantModel"] = relationship(back_populates="roles")
    role_permissions: Mapped[list["RolePermissionModel"]] = relationship(back_populates="role")
    user_roles: Mapped[list["UserRoleModel"]] = relationship(back_populates="role")


class PermissionModel(Base):
    """
    Permissões são GLOBAIS (compartilhadas por todos os tenants) — o
    catálogo de "o que o sistema é capaz de proteger" (ex: "voters:create",
    "finance:read") não muda entre campanhas, só QUAIS papéis têm QUAIS
    permissões muda (isso é `RolePermissionModel`, por tenant via `role`).
    Por isso esta tabela não tem `tenant_id`.
    """

    __tablename__ = "permissions"
    __table_args__ = (UniqueConstraint("resource", "action", name="uq_permissions_resource_action"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)

    role_permissions: Mapped[list["RolePermissionModel"]] = relationship(back_populates="permission")


class UserRoleModel(Base):
    """Tabela de associação N:N entre User e Role."""

    __tablename__ = "user_roles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped["UserModel"] = relationship(back_populates="user_roles")
    role: Mapped["RoleModel"] = relationship(back_populates="user_roles")


class RolePermissionModel(Base):
    """Tabela de associação N:N entre Role e Permission."""

    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )

    role: Mapped["RoleModel"] = relationship(back_populates="role_permissions")
    permission: Mapped["PermissionModel"] = relationship(back_populates="role_permissions")


class LeadershipModel(TimestampMixin, Base):
    __tablename__ = "leaderships"
    __table_args__ = (
        Index("ix_leaderships_tenant_id", "tenant_id"),
        Index("ix_leaderships_name", "name"),
        Index("ix_leaderships_region", "region"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str | None] = mapped_column(String(255))
    estimated_votes: Mapped[int] = mapped_column(nullable=False, default=0)
    influence_level: Mapped[str] = mapped_column(String(10), nullable=False)
    team_size: Mapped[int | None]
    notes: Mapped[str | None] = mapped_column(String)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EventModel(TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_tenant_id", "tenant_id"),
        Index("ix_events_starts_at", "starts_at"),
        Index("ix_events_status", "status"),
        Index("ix_events_voter_id", "voter_id"),
        Index("ix_events_leadership_id", "leadership_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    responsible_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default="agendado")
    location: Mapped[str | None] = mapped_column(String(500))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    voter_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("voters.id", ondelete="SET NULL"), nullable=True
    )
    leadership_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leaderships.id", ondelete="SET NULL"), nullable=True
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class VoterModel(TimestampMixin, Base):
    __tablename__ = "voters"
    __table_args__ = (
        Index("ix_voters_tenant_id", "tenant_id"),
        Index("ix_voters_name", "name"),
        Index("ix_voters_phone", "phone"),
        Index("ix_voters_tags", "tags", postgresql_using="gin"),
        Index("ix_voters_leadership_id", "leadership_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(500))
    city: Mapped[str | None] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(2))
    postal_code: Mapped[str | None] = mapped_column(String(20))
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(String)
    legal_basis: Mapped[str] = mapped_column(String(50), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    leadership_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("leaderships.id", ondelete="SET NULL"), nullable=True
    )


class FinanceTransactionModel(TimestampMixin, Base):
    __tablename__ = "finance_transactions"
    __table_args__ = (
        Index("ix_finance_transactions_tenant_id", "tenant_id"),
        Index("ix_finance_transactions_occurred_at", "occurred_at"),
        Index("ix_finance_transactions_type", "type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    # Numeric(12, 2): até 10 dígitos inteiros + 2 decimais (R$ 99.999.999,99
    # de teto) — SQLAlchemy mapeia Numeric para decimal.Decimal em Python
    # automaticamente, nunca float.
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(String)
    occurred_at: Mapped[date] = mapped_column(Date, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PlanModel(TimestampMixin, Base):
    """
    Catálogo GLOBAL de planos — sem tenant_id, sem RLS (mesmo padrão de
    PermissionModel, Módulo 1). Todo tenant enxerga o mesmo catálogo.
    """

    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    max_users: Mapped[int | None]
    max_voters: Mapped[int | None]
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class SubscriptionModel(TimestampMixin, Base):
    """
    Liga um tenant a um plano — TEM tenant_id, segue o padrão normal de
    RLS. `UniqueConstraint` em tenant_id: relação 1:1, um tenant tem no
    máximo uma assinatura por vez nesta versão.
    """

    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_subscriptions_tenant_id"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(15), nullable=False)
    current_period_end: Mapped[date] = mapped_column(Date, nullable=False)


class PlatformAdminModel(TimestampMixin, Base):
    """
    Usuário da PLATAFORMA (super-admin) — sem tenant_id, sem RLS, tabela
    completamente separada de UserModel. E-mail único GLOBALMENTE (não
    por tenant, diferente de UserModel).
    """

    __tablename__ = "platform_admins"
    __table_args__ = (UniqueConstraint("email", name="uq_platform_admins_email"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
