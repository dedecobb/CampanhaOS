"""
Implementação real de PlatformAdminTokenService.

Mesma chave secreta/algoritmo do JwtTokenService de usuário normal
(settings.jwt_secret_key), mas o campo "type" no payload usa um
namespace DIFERENTE ("platform_admin_access"/"platform_admin_refresh",
em vez de "access"/"refresh"). Isso é a barreira de segurança central
deste módulo: mesmo que alguém pegasse um token de usuário normal válido
e tentasse usá-lo aqui, `_decode` rejeitaria por causa do "type" errado
— e vice-versa.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt

from src.application.admin.ports import (
    PlatformAdminAccessTokenPayload,
    PlatformAdminRefreshTokenPayload,
    PlatformAdminTokenService,
)
from src.application.auth.exceptions import InvalidTokenError
from src.application.auth.ports import TokenPair
from src.config.settings import Settings
from src.domain.admin.entities import PlatformAdmin

_ACCESS_TOKEN_TYPE = "platform_admin_access"
_REFRESH_TOKEN_TYPE = "platform_admin_refresh"


class JwtPlatformAdminTokenService(PlatformAdminTokenService):
    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire_minutes = settings.access_token_expire_minutes
        self._refresh_expire_days = settings.refresh_token_expire_days

    def create_token_pair(self, admin: PlatformAdmin) -> TokenPair:
        now = datetime.now(UTC)

        access_payload = {
            "sub": str(admin.id),
            "type": _ACCESS_TOKEN_TYPE,
            "iat": now,
            "exp": now + timedelta(minutes=self._access_expire_minutes),
        }
        access_token = jwt.encode(access_payload, self._secret_key, algorithm=self._algorithm)

        refresh_payload = {
            "sub": str(admin.id),
            "type": _REFRESH_TOKEN_TYPE,
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(days=self._refresh_expire_days),
        }
        refresh_token = jwt.encode(refresh_payload, self._secret_key, algorithm=self._algorithm)

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def decode_access_token(self, token: str) -> PlatformAdminAccessTokenPayload:
        payload = self._decode(token)
        if payload.get("type") != _ACCESS_TOKEN_TYPE:
            raise InvalidTokenError("Token fornecido não é um access token de administrador")
        return PlatformAdminAccessTokenPayload(admin_id=UUID(payload["sub"]))

    def decode_refresh_token(self, token: str) -> PlatformAdminRefreshTokenPayload:
        payload = self._decode(token)
        if payload.get("type") != _REFRESH_TOKEN_TYPE:
            raise InvalidTokenError("Token fornecido não é um refresh token de administrador")
        return PlatformAdminRefreshTokenPayload(admin_id=UUID(payload["sub"]), jti=payload["jti"])

    def _decode(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError as exc:
            raise InvalidTokenError from exc
