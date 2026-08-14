"""
Exceções de domínio.

Regra do projeto: código de domínio nunca lança exceções genéricas do
Python (ValueError, Exception) para erros de regra de negócio — sempre uma
subclasse de DomainError. Isso permite que a camada de presentation (API)
saiba, com segurança de tipos, quando um erro é "regra de negócio violada"
(deve virar HTTP 400/409/422) versus um erro técnico inesperado (deve virar
HTTP 500 e ser logado como incidente).
"""


class DomainError(Exception):
    """Classe base para todo erro de regra de negócio do domínio."""


class InvalidEmailError(DomainError):
    def __init__(self, email: str) -> None:
        super().__init__(f"E-mail inválido: '{email}'")
        self.email = email


class InvalidNameError(DomainError):
    def __init__(self, message: str = "Nome não pode ser vazio") -> None:
        super().__init__(message)
