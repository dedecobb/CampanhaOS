"""
Porta (interface) do serviço de geocodificação.

Abstrai o provedor (Mapbox) atrás de uma interface — mesmo padrão de
`PasswordHasher`/`TokenService` (Módulo 1): a camada de aplicação nunca
importa o SDK/cliente HTTP do Mapbox diretamente, só esta interface.
Troca de provedor no futuro (ex: Google, HERE) significa só escrever uma
nova implementação em `infrastructure/`, sem tocar em `application/`.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class Coordinates:
    latitude: float
    longitude: float


class GeocodingService(ABC):
    @abstractmethod
    async def geocode(self, address: str) -> Coordinates | None:
        """
        Retorna as coordenadas do endereço, ou `None` se não conseguir
        geocodificar (endereço não encontrado, erro de rede, etc.) —
        NUNCA levanta exceção. Geocodificação é uma melhoria, não um
        requisito: se falhar, quem chama deve seguir em frente sem
        coordenada, não bloquear a operação (ex: criar um eleitor).
        """
