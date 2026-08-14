"""
Cliente Redis assíncrono compartilhado.

Redis é usado no projeto para 3 propósitos distintos (ADR-003): cache,
broker do Celery, e blocklist de refresh tokens (este módulo). Um único
client reaproveitado evita abrir conexões novas desnecessariamente.
"""

from redis.asyncio import Redis

from src.config.settings import get_settings

settings = get_settings()

redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)
