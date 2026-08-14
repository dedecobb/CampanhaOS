"""
Exceções da camada de aplicação (casos de uso de autenticação).

Diferente de `domain/shared/exceptions.py` (violação de invariante de uma
entidade), estas representam falhas de um FLUXO/caso de uso — ex: "as
credenciais não batem" não é uma regra que a entidade User quebra, é uma
decisão do caso de uso de login.
"""

from src.application.shared.exceptions import ApplicationError

__all__ = [
    "ApplicationError",
    "EmailAlreadyExistsError",
    "InvalidCredentialsError",
    "InvalidTokenError",
    "TenantNotAuthenticatableError",
    "WeakPasswordError",
]


class InvalidCredentialsError(ApplicationError):
    def __init__(self) -> None:
        # Mensagem propositalmente genérica — nunca revelar se foi o
        # e-mail ou a senha que estava errada, para não facilitar
        # enumeração de e-mails cadastrados por um atacante.
        super().__init__("E-mail ou senha inválidos")


class TenantNotAuthenticatableError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Esta campanha não está com acesso liberado no momento")


class EmailAlreadyExistsError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Já existe um usuário com este e-mail nesta campanha")


class InvalidTokenError(ApplicationError):
    def __init__(self, message: str = "Token inválido ou expirado") -> None:
        super().__init__(message)


class WeakPasswordError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("A senha precisa ter ao menos 8 caracteres")
