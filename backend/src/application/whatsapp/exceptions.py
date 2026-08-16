from src.application.shared.exceptions import ApplicationError


class WhatsAppContactNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__("Contato de WhatsApp não encontrado")


class ContactNotOptedInError(ApplicationError):
    def __init__(self) -> None:
        # Mensagem deliberadamente explícita sobre O PORQUÊ — quem for
        # debugar isso no futuro precisa entender que essa não é uma
        # trava técnica arbitrária, é a regra de negócio central do
        # módulo inteiro (ver ADR de compliance, documento fonte da
        # verdade).
        super().__init__(
            "Não é possível enviar mensagem: este contato não deu opt-in "
            "(ou já se descadastrou). Envio de mensagem político-eleitoral "
            "sem consentimento explícito é proibido pela Resolução TSE "
            "23.610/2019."
        )
