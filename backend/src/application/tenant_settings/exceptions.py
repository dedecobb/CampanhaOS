from src.application.shared.exceptions import ApplicationError


class InvalidRegistrationTokenError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Link de autocadastro inválido ou desativado")


class RegistrationRateLimitExceededError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Muitas tentativas de cadastro em pouco tempo. Tente novamente mais tarde.")
