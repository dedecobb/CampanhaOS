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
    async def geocode(
        self,
        address_line: str,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        neighborhood: str | None = None,
    ) -> Coordinates | None:
        """
        Recebe os campos do endereço SEPARADOS (não uma string única
        concatenada) — implementações devem repassar cada campo pro seu
        parâmetro próprio na API do provedor, quando o provedor suportar
        entrada estruturada (Mapbox v6 suporta; concatenar tudo numa
        string só, como fizemos numa primeira tentativa, gerou resultado
        impreciso na prática — ver documento fonte da verdade).

        Retorna `None` se não conseguir geocodificar (endereço não
        encontrado, erro de rede, etc.) — NUNCA levanta exceção.
        Geocodificação é uma melhoria, não um requisito: se falhar, quem
        chama deve seguir em frente sem coordenada, não bloquear a
        operação (ex: criar um eleitor).
        """
