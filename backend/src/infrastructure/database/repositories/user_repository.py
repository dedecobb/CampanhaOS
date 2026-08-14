"""
Implementação concreta de UserRepository (porta definida em
`domain/users/repository.py`), usando SQLAlchemy async + PostgreSQL.

Responsabilidade extra deste arquivo, além de persistir dados: traduzir
entre `UserModel` (representação de banco) e `User` (entidade de domínio),
nos dois sentidos. Nenhuma outra camada do sistema deve fazer essa
tradução — é o único lugar que conhece os dois mundos ao mesmo tempo.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.users.entities import User
from src.domain.users.repository import UserRepository
from src.domain.users.value_objects import Email
from src.infrastructure.database.models import RoleModel, UserModel, UserRoleModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, user: User) -> None:
        existing = await self._session.get(UserModel, user.id)
        if existing is None:
            model = UserModel(
                id=user.id,
                tenant_id=user.tenant_id,
                name=user.name,
                email=str(user.email),
                password_hash=user.password_hash,
                is_active=user.is_active,
            )
            self._session.add(model)
        else:
            # Atualiza apenas os campos que a entidade de domínio permite
            # mudar (name, is_active) — email e password_hash têm fluxos
            # próprios (troca de e-mail e troca de senha) que serão casos
            # de uso dedicados mais à frente, não um save genérico.
            existing.name = user.name
            existing.is_active = user.is_active

        # Nota: `flush()` envia o SQL para o banco mas não faz commit —
        # quem decide o momento do commit é o caso de uso (camada
        # `application`), não o repository. Isso é o que permite um caso de
        # uso compor múltiplas operações de repositório numa única
        # transação atômica.
        await self._session.flush()

    async def find_by_id(self, tenant_id: UUID, user_id: UUID) -> User | None:
        stmt = select(UserModel).where(
            UserModel.id == user_id,
            UserModel.tenant_id == tenant_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_email(self, tenant_id: UUID, email: Email) -> User | None:
        stmt = select(UserModel).where(
            UserModel.email == str(email),
            UserModel.tenant_id == tenant_id,
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def email_exists(self, tenant_id: UUID, email: Email) -> bool:
        stmt = select(UserModel.id).where(
            UserModel.email == str(email),
            UserModel.tenant_id == tenant_id,
        )
        result = (await self._session.execute(stmt)).scalar_one_or_none()
        return result is not None

    async def _load_role_names(self, user_id: UUID) -> list[str]:
        stmt = (
            select(RoleModel.name)
            .join(UserRoleModel, UserRoleModel.role_id == RoleModel.id)
            .where(UserRoleModel.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    def _to_domain(self, model: UserModel) -> User:
        """
        Reconstrói a entidade de domínio a partir do model de banco.

        Nota de limitação consciente: esta versão não carrega `role_names`
        automaticamente (para não forçar uma query extra em todo find_by_*
        onde papéis não são necessários). Casos de uso que precisam dos
        papéis do usuário devem chamar `_load_role_names` explicitamente —
        vamos revisitar isso caso vire um padrão repetitivo demais nos
        próximos módulos, e nesse caso valeria um método dedicado tipo
        `find_by_id_with_roles`.
        """
        return User(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            email=Email(model.email),
            password_hash=model.password_hash,
            is_active=model.is_active,
            created_at=model.created_at,
            role_names=[],
        )
