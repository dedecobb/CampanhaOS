from src.application.shared.exceptions import ApplicationError


class InvalidAdminCredentialsError(ApplicationError):
    def __init__(self) -> None:
        # Mesma disciplina do auth de usuário normal (Módulo 1): mensagem
        # genérica, nunca revela se foi o e-mail ou a senha.
        super().__init__("E-mail ou senha inválidos")


class TenantNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Campanha (tenant) não encontrada")