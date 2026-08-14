"""
Caso de uso: login.

Fluxo: valida que o tenant existe e está apto a autenticar (RN registrada
na entidade Tenant: `can_authenticate`), valida credenciais do usuário, e
emite um par de tokens (access + refresh) via TokenService.
"""

from src.application.auth.dto import LoginInput, LoginOutput
from src.application.auth.exceptions import InvalidCredentialsError, TenantNotAuthenticatableError
from src.application.auth.ports import PasswordHasher, TenantContextSetter, TokenService
from src.domain.tenants.repository import TenantRepository
from src.domain.users.repository import UserRepository
from src.domain.users.value_objects import Email


class LoginUseCase:
    def __init__(
        self,
        tenant_repository: TenantRepository,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        tenant_context_setter: TenantContextSetter,
    ) -> None:
        self._tenant_repository = tenant_repository
        self._user_repository = user_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._tenant_context_setter = tenant_context_setter

    async def execute(self, input_data: LoginInput) -> LoginOutput:
        tenant = await self._tenant_repository.find_by_id(input_data.tenant_id)
        if tenant is None or not tenant.can_authenticate:
            # Mesma mensagem genérica de credenciais inválidas seria
            # excessiva aqui — "campanha suspensa" é uma informação legítima
            # de mostrar (não vaza dado de outro usuário/tenant).
            raise TenantNotAuthenticatableError

        # A partir daqui sabemos qual tenant está sendo operado — necessário
        # antes de tocar em `users` (RLS).
        await self._tenant_context_setter.set_context(tenant.id)

        try:
            email = Email(input_data.email)
        except Exception as exc:  # noqa: BLE001 - convertido para erro de aplicação abaixo
            raise InvalidCredentialsError from exc

        user = await self._user_repository.find_by_email(tenant.id, email)
        if user is None or not user.is_active:
            raise InvalidCredentialsError

        if not self._password_hasher.verify(input_data.password, user.password_hash):
            raise InvalidCredentialsError

        token_pair = self._token_service.create_token_pair(user)
        return LoginOutput(access_token=token_pair.access_token, refresh_token=token_pair.refresh_token)
