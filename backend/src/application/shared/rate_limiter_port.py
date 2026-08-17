"""
Porta (interface) de limitação de taxa.

Usada para proteger o endpoint PÚBLICO de autocadastro contra spam/bot —
sem isso, qualquer script poderia encher a base de eleitores com
registros falsos, já que esse endpoint não exige login.
"""

from abc import ABC, abstractmethod


class RateLimiter(ABC):
    @abstractmethod
    async def check_and_consume(self, key: str, max_per_window: int, window_seconds: int) -> bool:
        """
        Retorna `True` se ainda há cota disponível para essa `key` dentro
        da janela de tempo — e, se retornar `True`, já CONSOME uma
        unidade dessa cota (operação atômica: verificar e consumir juntos,
        para não abrir brecha de "duas requisições simultâneas passando
        pela checagem antes de qualquer uma delas contar").
        """
