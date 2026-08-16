"""
Entidade de domínio: Voter (Eleitor).

Campos personalizáveis (RF-04, decisão da Fase 1): em vez de um schema
dinâmico (EAV), usamos `tags` (lista simples) + `custom_fields` (chave-
valor livre) — resolve a maioria dos casos reais sem a complexidade de um
schema verdadeiramente dinâmico.

RN-05 (Fase 1): todo dado pessoal de eleitor precisa de uma base legal
(LGPD) registrada — por isso `legal_basis` é obrigatório na criação, não
opcional.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.shared.exceptions import DomainError, InvalidNameError

_VALID_LEGAL_BASES = frozenset(
    {
        "consentimento",
        "obrigacao_legal",
        "execucao_de_contrato",
        "interesse_legitimo",
        "protecao_da_vida",
        "exercicio_regular_de_direitos",
    }
)


class InvalidLegalBasisError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(
            f"Base legal '{value}' inválida. Valores aceitos: {', '.join(sorted(_VALID_LEGAL_BASES))}"
        )


_UNSET = object()  # sentinela: distingue "não foi passado" de "foi passado como None"


@dataclass
class Voter:
    id: UUID
    tenant_id: UUID
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
    deleted_at: datetime | None = None
    leadership_id: UUID | None = None

    @staticmethod
    def create(
        tenant_id: UUID,
        created_by_user_id: UUID,
        name: str,
        legal_basis: str,
        phone: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        tags: list[str] | None = None,
        custom_fields: dict[str, str] | None = None,
        notes: str | None = None,
        leadership_id: UUID | None = None,
    ) -> "Voter":
        Voter._validate_name(name)
        Voter._validate_legal_basis(legal_basis)

        now = datetime.now(UTC)
        return Voter(
            id=uuid4(),
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            name=name.strip(),
            phone=phone.strip() if phone else None,
            address=address.strip() if address else None,
            city=city.strip() if city else None,
            state=state.strip().upper() if state else None,  # sigla de UF, ex: "RJ" — normaliza maiúscula
            postal_code=postal_code.strip() if postal_code else None,
            latitude=latitude,
            longitude=longitude,
            tags=sorted(set(tags)) if tags else [],  # sem duplicatas, ordem estável
            custom_fields=custom_fields or {},
            notes=notes,
            legal_basis=legal_basis,
            created_at=now,
            updated_at=now,
            deleted_at=None,
            leadership_id=leadership_id,
        )

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise InvalidNameError("Nome do eleitor não pode ser vazio")

    @staticmethod
    def _validate_legal_basis(legal_basis: str) -> None:
        if legal_basis not in _VALID_LEGAL_BASES:
            raise InvalidLegalBasisError(legal_basis)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def geocoding_query(self) -> str | None:
        """
        Monta a string completa usada para geocodificar — combinar
        endereço + cidade + estado + CEP resolve a ambiguidade que um
        endereço sozinho tem (ex: "Rua das Flores, 123" existe em
        centenas de cidades brasileiras diferentes; com cidade/estado/CEP
        juntos, o geocodificador consegue ser preciso).
        """
        if not self.address:
            return None
        parts = [self.address]
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.postal_code:
            parts.append(self.postal_code)
        return ", ".join(parts) + ", Brasil"

    def update_details(
        self,
        *,
        name: str | None = None,
        phone: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        postal_code: str | None = None,
        latitude: float | None = None,
        longitude: float | None = None,
        tags: list[str] | None = None,
        custom_fields: dict[str, str] | None = None,
        notes: str | None = None,
        leadership_id: UUID | None = _UNSET,  # type: ignore[assignment]
    ) -> None:
        """
        Atualização parcial: só os campos explicitamente passados (≠ None
        do valor "sentinela" de "não alterar") são modificados. Como
        `phone`/`address`/`notes` podem legitimamente ser apagados (setados
        para vazio), a convenção aqui é: quem chama passa string vazia
        para limpar um campo, e realmente não passa o argumento (usa o
        default) para "não mexer nisso".

        `leadership_id` é diferente dos demais: `None` é um valor VÁLIDO
        (significa "remover a associação com a liderança"), então não pode
        usar `None` como "não foi passado" — por isso usa um sentinela
        próprio (`_UNSET`) só para este campo.
        """
        if name is not None:
            Voter._validate_name(name)
            self.name = name.strip()
        if phone is not None:
            self.phone = phone.strip() or None
        if address is not None:
            self.address = address.strip() or None
        if city is not None:
            self.city = city.strip() or None
        if state is not None:
            self.state = state.strip().upper() or None
        if postal_code is not None:
            self.postal_code = postal_code.strip() or None
        if latitude is not None:
            self.latitude = latitude
        if longitude is not None:
            self.longitude = longitude
        if tags is not None:
            self.tags = sorted(set(tags))
        if custom_fields is not None:
            self.custom_fields = custom_fields
        if notes is not None:
            self.notes = notes or None
        if leadership_id is not _UNSET:
            self.leadership_id = leadership_id

        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)
