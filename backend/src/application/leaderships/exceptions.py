from src.application.shared.exceptions import ApplicationError


class LeadershipNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Liderança não encontrada")
