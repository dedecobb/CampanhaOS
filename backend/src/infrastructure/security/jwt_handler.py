"""
Implementação real de TokenService usando JWT (via python-jose).

Dois tipos de token, diferenciados pelo campo "type" dentro do payload:
- access: vida curta (settings.access_token_expire_minutes), enviado em
  toda requisição autenticada.
- refresh: vida longa (settings.refresh_token_expire_days), usado só para
  obter um novo access token, e carrega um "jti" (JWT ID) que permite
  revogação individual via RefreshTokenBlocklist.

Nunca aceitamos um refresh token como se fosse access token ou vice-versa
— o campo "type" é validado explicitamente em cada decode.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from jose import JWTError, jwt

from src.application.auth.exceptions import InvalidTokenError
from src.application.auth.ports import AccessTokenPayload, RefreshTokenPayload, TokenPair, TokenService
from src.config.settings import Settings
from src.domain.users.entities import User


class JwtTokenService(TokenService):
    def __init__(self, settings: Settings) -> None:
        self._secret_key = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire_minutes = settings.access_token_expire_minutes
        self._refresh_expire_days = settings.refresh_token_expire_days

    def create_token_pair(self, user: User) -> TokenPair:
        now = datetime.now(UTC)

        access_payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "roles": user.role_names,
            "type": "access",
            "iat": now,
            "exp": now + timedelta(minutes=self._access_expire_minutes),
        }
        access_token = jwt.encode(access_payload, self._secret_key, algorithm=self._algorithm)

        refresh_payload = {
            "sub": str(user.id),
            "tenant_id": str(user.tenant_id),
            "type": "refresh",
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(days=self._refresh_expire_days),
        }
        refresh_token = jwt.encode(refresh_payload, self._secret_key, algorithm=self._algorithm)

        return TokenPair(access_token=access_token, refresh_token=refresh_token)

    def decode_access_token(self, token: str) -> AccessTokenPayload:
        payload = self._decode(token)
        if payload.get("type") != "access":
            raise InvalidTokenError("Token fornecido não é um access token")
        return AccessTokenPayload(
            user_id=UUID(payload["sub"]),
            tenant_id=UUID(payload["tenant_id"]),
            role_names=payload.get("roles", []),
        )

    def decode_refresh_token(self, token: str) -> RefreshTokenPayload:
        payload = self._decode(token)
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Token fornecido não é um refresh token")
        return RefreshTokenPayload(
            user_id=UUID(payload["sub"]),
            tenant_id=UUID(payload["tenant_id"]),
            jti=payload["jti"],
        )

    def _decode(self, token: str) -> dict:
        try:
            return jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except JWTError as exc:
            # Cobre assinatura inválida, token expirado e token malformado
            # — python-jose levanta subclasses diferentes de JWTError para
            # cada caso, mas para o resto do sistema todos são igualmente
            # "token inválido", então unificamos aqui.
            raise InvalidTokenError from exc
