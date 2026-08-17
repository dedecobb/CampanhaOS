"""
Implementação concreta de RateLimiter usando Redis.

Algoritmo "janela fixa" (fixed window): a primeira requisição de uma
chave cria um contador com expiração igual à janela; cada requisição
seguinte incrementa esse contador; se passar do limite, rejeita. Mais
simples que "janela deslizante" (sliding window) — para o volume de um
formulário público de campanha, essa simplicidade é suficiente, não
precisa da precisão extra de um algoritmo mais sofisticado.
"""

from redis.asyncio import Redis

from src.application.shared.rate_limiter_port import RateLimiter

_KEY_PREFIX = "rate_limit:"


class RedisRateLimiter(RateLimiter):
    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    async def check_and_consume(self, key: str, max_per_window: int, window_seconds: int) -> bool:
        redis_key = f"{_KEY_PREFIX}{key}"

        # INCR cria a chave com valor 1 se não existir, ou incrementa se
        # já existir — operação atômica no Redis, não tem "corrida" entre
        # duas requisições simultâneas lendo o valor antigo antes de
        # escrever o novo.
        current_count = await self._redis.incr(redis_key)

        if current_count == 1:
            # Só define a expiração na PRIMEIRA requisição da janela —
            # se definíssemos em toda chamada, a janela nunca "fecharia"
            # de verdade (ficaria sempre se renovando a cada requisição).
            await self._redis.expire(redis_key, window_seconds)

        return current_count <= max_per_window
