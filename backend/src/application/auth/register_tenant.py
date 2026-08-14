"""
Caso de uso: registrar uma nova campanha (tenant) com seu usuário
administrador inicial.

Nota de escopo (registrada também no documento fonte da verdade): este
caso de uso NÃO atribui um papel (Role) ao usuário criado — RBAC completo
(criação de papéis padrão por tenant, atribuição automática de "admin")
fica para o módulo de gerenciamento de equipe. Por ora, o usuário existe e
consegue logar, mas ainda sem permissões granulares aplicadas.
"""

from src.application.auth.dto import RegisterTenantInput, RegisterTenantOutput
from src.application.auth.exceptions import EmailAlreadyExistsError, WeakPasswordError
from src.application.auth.ports import PasswordHasher, TenantContextSetter
from src.domain.tenants.entities import Tenant
from src.domain.tenants.repository import TenantRepository
from src.domain.users.entities import User
from src.domain.users.repository import UserRepository
from src.domain.users.value_objects import Email

_MIN_PASSWORD_LENGTH = 8


class RegisterTenantUseCase:
    def __init__(
        self,
        tenant_repository: TenantRepository,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        tenant_context_setter: TenantContextSetter,
    ) -> None:
        self._tenant_repository = tenant_repository
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._tenant_context_setter = tenant_context_setter

    async def execute(self, input_data: RegisterTenantInput) -> RegisterTenantOutput:
        # Validação de política de senha: preocupação do CASO DE USO (é uma
        # regra sobre o processo de cadastro), não da entidade User em si
        # (a entidade User não sabe nem deveria saber sobre "senha em texto
        # plano" — ela só guarda o hash já pronto).
        if len(input_data.admin_password) < _MIN_PASSWORD_LENGTH:
            raise WeakPasswordError

        email = Email(input_data.admin_email)  # levanta InvalidEmailError se malformado

        tenant = Tenant.create(name=input_data.tenant_name)  # levanta InvalidNameError se inválido
        await self._tenant_repository.save(tenant)

        # A partir daqui, a transação está "operando" sobre este tenant —
        # necessário porque a tabela `users` tem RLS e exigiria isso mesmo
        # sem nenhuma autenticação prévia (ver explicação da porta).
        await self._tenant_context_setter.set_context(tenant.id)

        if await self._user_repository.email_exists(tenant.id, email):
            # Defensivo: tenant acabou de ser criado, então isso é
            # praticamente impossível na prática (colisão de UUID), mas
            # manter a checagem custa pouco e documenta a invariante.
            raise EmailAlreadyExistsError

        password_hash = self._password_hasher.hash(input_data.admin_password)
        user = User.create(
            tenant_id=tenant.id,
            name=input_data.admin_name,
            email=email,
            password_hash=password_hash,
        )
        await self._user_repository.save(user)

        return RegisterTenantOutput(tenant_id=tenant.id, user_id=user.id)
