from src.application.admin.dto import AdminLoginInput, AdminLoginOutput
from src.application.admin.exceptions import InvalidAdminCredentialsError
from src.application.admin.ports import PlatformAdminTokenService
from src.application.auth.ports import PasswordHasher
from src.domain.admin.repository import PlatformAdminRepository
from src.domain.users.value_objects import Email


class AdminLoginUseCase:
    def __init__(
        self,
        platform_admin_repository: PlatformAdminRepository,
        password_hasher: PasswordHasher,
        token_service: PlatformAdminTokenService,
    ) -> None:
        self._platform_admin_repository = platform_admin_repository
        self._password_hasher = password_hasher
        self._token_service = token_service

    async def execute(self, input_data: AdminLoginInput) -> AdminLoginOutput:
        try:
            email = Email(input_data.email)
        except Exception as exc:  # noqa: BLE001 - convertido para erro de aplicação abaixo
            raise InvalidAdminCredentialsError from exc

        admin = await self._platform_admin_repository.find_by_email(email)
        if admin is None or not admin.is_active:
            raise InvalidAdminCredentialsError

        if not self._password_hasher.verify(input_data.password, admin.password_hash):
            raise InvalidAdminCredentialsError

        token_pair = self._token_service.create_token_pair(admin)
        return AdminLoginOutput(access_token=token_pair.access_token, refresh_token=token_pair.refresh_token)
