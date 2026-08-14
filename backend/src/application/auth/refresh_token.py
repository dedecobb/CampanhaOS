"""
Caso de uso: renovar tokens a partir de um refresh token válido.

Implementa ROTAÇÃO de refresh token: cada vez que um refresh token é
usado, ele é imediatamente revogado (adicionado à blocklist) e um par
novo é emitido. Isso significa que um refresh token só pode ser usado
UMA VEZ — se um token roubado for reutilizado depois do dono legítimo já
ter renovado, a tentativa falha (o token antigo já está revogado), o que
é um sinal de possível token comprometido.
"""

from src.application.auth.dto import RefreshTokenInput, RefreshTokenOutput
from src.application.auth.exceptions import InvalidTokenError
from src.application.auth.ports import RefreshTokenBlocklist, TenantContextSetter, TokenService
from src.domain.users.repository import UserRepository


class RefreshTokenUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        token_service: TokenService,
        refresh_token_blocklist: RefreshTokenBlocklist,
        tenant_context_setter: TenantContextSetter,
        refresh_token_ttl_seconds: int,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service
        self._refresh_token_blocklist = refresh_token_blocklist
        self._tenant_context_setter = tenant_context_setter
        self._refresh_token_ttl_seconds = refresh_token_ttl_seconds

    async def execute(self, input_data: RefreshTokenInput) -> RefreshTokenOutput:
        payload = self._token_service.decode_refresh_token(input_data.refresh_token)

        if await self._refresh_token_blocklist.is_revoked(payload.jti):
            raise InvalidTokenError("Este refresh token já foi utilizado ou revogado")

        # Só agora sabemos o tenant (veio de dentro do token) — necessário
        # antes de tocar em `users` (RLS).
        await self._tenant_context_setter.set_context(payload.tenant_id)

        user = await self._user_repository.find_by_id(payload.tenant_id, payload.user_id)
        if user is None or not user.is_active:
            raise InvalidTokenError("Usuário não encontrado ou inativo")

        # Rotação: revoga o token que acabou de ser usado ANTES de emitir o
        # novo par — mesmo que algo falhe depois, o token antigo já não
        # pode mais ser reaproveitado.
        await self._refresh_token_blocklist.revoke(payload.jti, self._refresh_token_ttl_seconds)

        new_pair = self._token_service.create_token_pair(user)
        return RefreshTokenOutput(access_token=new_pair.access_token, refresh_token=new_pair.refresh_token)
