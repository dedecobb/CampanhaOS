from src.application.shared.exceptions import ApplicationError


class PlanNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Plano não encontrado")


class InactivePlanError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Este plano não está mais disponível")
