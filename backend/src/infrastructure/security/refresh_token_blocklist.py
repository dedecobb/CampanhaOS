"""
Implementação real de RefreshTokenBlocklist usando Redis.

Decisão de design: usamos `SETEX` (set com expiração) em vez de guardar a
entrada indefinidamente. O TTL passado pelo caso de uso corresponde ao
tempo restante de vida do próprio refresh token — não faz sentido manter
um jti na blocklist depois que o token já expiraria de qualquer forma por
conta própria. Isso mantém o Redis enxuto automaticamente, sem precisar de
um job de limpeza separado.
"""

from redis.asyncio import Redis

from src.application.auth.ports import RefreshTokenBlocklist

_KEY_PREFIX = "revoked_refresh_token:"


class RedisRefreshTokenBlocklist(RefreshTokenBlocklist):
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def revoke(self, jti: str, ttl_seconds: int) -> None:
        await self._redis.setex(f"{_KEY_PREFIX}{jti}", ttl_seconds, "1")

    async def is_revoked(self, jti: str) -> bool:
        exists = await self._redis.exists(f"{_KEY_PREFIX}{jti}")
        return exists == 1
