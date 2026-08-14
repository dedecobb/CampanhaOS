from src.application.shared.exceptions import ApplicationError


class FinanceTransactionNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Lançamento financeiro não encontrado")
