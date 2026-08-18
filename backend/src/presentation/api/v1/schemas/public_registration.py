"""
Schemas dos endpoints PÚBLICOS de autocadastro — sem autenticação.
"""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

GenderLiteral = Literal["feminino", "masculino", "nao_binario", "prefere_nao_informar", "outro"]


class PublicCampaignInfoResponse(BaseModel):
    """Retornado pelo GET — só o necessário pra tela pública mostrar 'Cadastro para [Campanha]', nada sensível."""

    tenant_name: str


class PublicVoterRegistrationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    consent_given: bool = Field(
        ..., description="Precisa ser true — a pessoa precisa confirmar que concorda em fornecer os dados"
    )
    phone: str | None = Field(None, max_length=30)
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=255)
    state: str | None = Field(None, min_length=2, max_length=2)
    postal_code: str | None = Field(None, max_length=20)
    neighborhood: str | None = Field(None, max_length=255)
    gender: GenderLiteral | None = None
    birth_date: date | None = None
    # Vem do link específico de uma liderança (?lideranca={id}) — o
    # frontend lê da URL e manda aqui; None quando é o link geral da
    # campanha. Validado de verdade no caso de uso (ver
    # public_self_register.py) — um id inválido/de outro tenant não
    # bloqueia o cadastro, só não vincula.
    leadership_id: UUID | None = None


class PublicVoterRegistrationResponse(BaseModel):
    """
    Resposta deliberadamente MÍNIMA — a pessoa que se autocadastrou não
    precisa (nem deveria) ver de volta todos os campos que ela mandou,
    nem nenhum dado interno do sistema (id de tenant, etc.).
    """

    success: bool
    message: str
