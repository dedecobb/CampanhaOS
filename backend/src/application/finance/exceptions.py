from src.application.shared.exceptions import ApplicationError


class FinanceTransactionNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Lançamento financeiro não encontrado")


class NoAttachmentError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Este lançamento não tem nenhum anexo")


class UnsupportedFileTypeError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Tipo de arquivo não reconhecido — apenas JPEG, PNG ou PDF são aceitos")
