"""
Schemas Pydantic dos endpoints de eleitores.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# Espelha exatamente o conjunto de bases legais válidas do domínio
# (src/domain/voters/entities.py) — mantido em sincronia manualmente por
# enquanto; se a lista crescer, vale extrair para um lugar compartilhado.
LegalBasis = Literal[
    "consentimento",
    "obrigacao_legal",
    "execucao_de_contrato",
    "interesse_legitimo",
    "protecao_da_vida",
    "exercicio_regular_de_direitos",
]


class VoterCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    legal_basis: LegalBasis
    phone: str | None = Field(None, max_length=30)
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=255)
    state: str | None = Field(None, min_length=2, max_length=2, description="Sigla da UF, ex: RJ")
    postal_code: str | None = Field(None, max_length=20)
    latitude: float | None = None
    longitude: float | None = None
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, str] = Field(default_factory=dict)
    notes: str | None = None
    leadership_id: UUID | None = None


class VoterUpdateRequest(BaseModel):
    """
    Todos os campos opcionais — semântica de atualização parcial (PATCH).
    `None` = "não alterar este campo", espelhando a convenção já definida
    em `Voter.update_details` (domínio) — COM UMA EXCEÇÃO: `leadership_id`
    aceita `None` como valor válido (remover associação). O router
    (v1/routers/voters.py) usa `request.model_fields_set` para distinguir
    "campo omitido do JSON" de "campo enviado como null" antes de repassar
    para o caso de uso.
    """

    name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, max_length=30)
    address: str | None = Field(None, max_length=500)
    city: str | None = Field(None, max_length=255)
    state: str | None = Field(None, min_length=2, max_length=2)
    postal_code: str | None = Field(None, max_length=20)
    latitude: float | None = None
    longitude: float | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, str] | None = None
    notes: str | None = None
    leadership_id: UUID | None = None


class VoterResponse(BaseModel):
    # from_attributes=True: permite construir a resposta diretamente a
    # partir do VoterOutput (dataclass da camada de aplicação), sem
    # precisar converter campo a campo manualmente em cada endpoint.
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by_user_id: UUID
    name: str
    phone: str | None
    address: str | None
    city: str | None
    state: str | None
    postal_code: str | None
    latitude: float | None
    longitude: float | None
    tags: list[str]
    custom_fields: dict[str, str]
    notes: str | None
    legal_basis: str
    created_at: datetime
    updated_at: datetime
    leadership_id: UUID | None


class VoterListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[VoterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class VoterMapPointResponse(BaseModel):
    """Saída leve para a tela de mapa — ver VoterMapPointOutput (camada de aplicação)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    address: str | None
    latitude: float
    longitude: float
