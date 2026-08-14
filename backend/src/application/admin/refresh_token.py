from src.application.admin.dto import AdminRefreshTokenInput, AdminRefreshTokenOutput
from src.application.admin.ports import PlatformAdminTokenService
from src.application.auth.exceptions import InvalidTokenError
from src.application.auth.ports import RefreshTokenBlocklist
from src.domain.admin.repository import PlatformAdminRepository


class AdminRefreshTokenUseCase:
    """
    Mesma lógica de rotação de refresh token do Módulo 1
    (RefreshTokenUseCase) — reaproveita a MESMA porta `RefreshTokenBlocklist`
    (genérica o suficiente: só lida com `jti`, não sabe se é token de
    usuário ou de admin) e a MESMA exceção `InvalidTokenError` (também
    genérica).
    """

    def __init__(
        self,
        platform_admin_repository: PlatformAdminRepository,
        token_service: PlatformAdminTokenService,
        refresh_token_blocklist: RefreshTokenBlocklist,
        refresh_token_ttl_seconds: int,
    ) -> None:
        self._platform_admin_repository = platform_admin_repository
        self._token_service = token_service
        self._refresh_token_blocklist = refresh_token_blocklist
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds

    async def execute(self, input_data: AdminRefreshTokenInput) -> AdminRefreshTokenOutput:
        payload = self._token_service.decode_refresh_token(input_data.refresh_token)

        if await self._refresh_token_blocklist.is_revoked(payload.jti):
            raise InvalidTokenError("Este refresh token já foi utilizado ou revogado")

        admin = await self._platform_admin_repository.find_by_id(payload.admin_id)
        if admin is None or not admin.is_active:
            raise InvalidTokenError("Administrador não encontrado ou inativo")

        await self._refresh_token_blocklist.revoke(payload.jti, self._refresh_token_ttl_seconds)

        new_pair = self._token_service.create_token_pair(admin)
        return AdminRefreshTokenOutput(access_token=new_pair.access_token, refresh_token=new_pair.refresh_token)
