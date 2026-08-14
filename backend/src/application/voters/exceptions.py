"""
Exceções da camada de aplicação (casos de uso de eleitores).
"""

from src.application.shared.exceptions import ApplicationError


class VoterNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Eleitor não encontrado")
