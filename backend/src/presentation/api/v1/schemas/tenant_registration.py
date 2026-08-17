from pydantic import BaseModel


class RegistrationTokenResponse(BaseModel):
    token: str | None
    # Já monta o link completo de propósito — evita a campanha precisar
    # saber concatenar isso na mão. `None` quando o token também é `None`
    # (autocadastro desativado).
    registration_url: str | None
