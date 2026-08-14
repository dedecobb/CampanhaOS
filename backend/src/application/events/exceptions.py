from src.application.shared.exceptions import ApplicationError


class EventNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Evento não encontrado")


class ResponsibleUserNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Usuário responsável não encontrado nesta campanha")
