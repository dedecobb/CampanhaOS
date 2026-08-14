"""
Entidade de domínio: Event (Agenda).

RF-06 (Fase 1): eventos, reuniões e visitas da campanha. Pode
opcionalmente estar associado a um Eleitor (ex: "visita ao eleitor X") e/ou
a uma Liderança (ex: "reunião com a liderança Y") — mesmo padrão de
associação opcional com sentinela já validado no Módulo 3 para
`Voter.leadership_id`.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.shared.exceptions import DomainError, InvalidNameError

_VALID_EVENT_TYPES = frozenset({"evento", "reuniao", "visita"})
_VALID_STATUSES = frozenset({"agendado", "concluido", "cancelado"})

_UNSET = object()  # sentinela: "não foi passado" ≠ "foi passado como None"


class InvalidEventTypeError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(
            f"Tipo de evento '{value}' inválido. Valores aceitos: {', '.join(sorted(_VALID_EVENT_TYPES))}"
        )


class InvalidEventStatusError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(
            f"Status '{value}' inválido. Valores aceitos: {', '.join(sorted(_VALID_STATUSES))}"
        )


class InvalidEventPeriodError(DomainError):
    def __init__(self) -> None:
        super().__init__("A data/hora de término não pode ser anterior à data/hora de início")


@dataclass
class Event:
    id: UUID
    tenant_id: UUID
    created_by_user_id: UUID
    responsible_user_id: UUID
    title: str
    description: str | None
    event_type: str
    status: str
    location: str | None
    starts_at: datetime
    ends_at: datetime | None
    voter_id: UUID | None
    leadership_id: UUID | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @staticmethod
    def create(
        tenant_id: UUID,
        created_by_user_id: UUID,
        responsible_user_id: UUID,
        title: str,
        event_type: str,
        starts_at: datetime,
        description: str | None = None,
        location: str | None = None,
        ends_at: datetime | None = None,
        voter_id: UUID | None = None,
        leadership_id: UUID | None = None,
    ) -> "Event":
        Event._validate_title(title)
        Event._validate_event_type(event_type)
        Event._validate_period(starts_at, ends_at)

        now = datetime.now(UTC)
        return Event(
            id=uuid4(),
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            responsible_user_id=responsible_user_id,
            title=title.strip(),
            description=description,
            event_type=event_type,
            status="agendado",
            location=location.strip() if location else None,
            starts_at=starts_at,
            ends_at=ends_at,
            voter_id=voter_id,
            leadership_id=leadership_id,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    @staticmethod
    def _validate_title(title: str) -> None:
        if not title or not title.strip():
            raise InvalidNameError("Título do evento não pode ser vazio")

    @staticmethod
    def _validate_event_type(event_type: str) -> None:
        if event_type not in _VALID_EVENT_TYPES:
            raise InvalidEventTypeError(event_type)

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in _VALID_STATUSES:
            raise InvalidEventStatusError(status)

    @staticmethod
    def _validate_period(starts_at: datetime, ends_at: datetime | None) -> None:
        if ends_at is not None and ends_at < starts_at:
            raise InvalidEventPeriodError

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def update_details(
        self,
        *,
        title: str | None = None,
        description: str | None = None,
        event_type: str | None = None,
        status: str | None = None,
        location: str | None = None,
        starts_at: datetime | None = None,
        ends_at: datetime | None = None,
        responsible_user_id: UUID | None = None,
        voter_id: UUID | None = _UNSET,  # type: ignore[assignment]
        leadership_id: UUID | None = _UNSET,  # type: ignore[assignment]
    ) -> None:
        """
        `voter_id`/`leadership_id` usam o sentinela `_UNSET` (None é valor
        válido = "remover associação"). Os demais campos seguem a
        convenção já usada em Voter/Leadership: None = "não alterar".

        `starts_at`/`ends_at` são validados juntos, sempre com o par final
        (novo ou mantido), nunca comparando um valor novo com um antigo
        de forma inconsistente.
        """
        new_starts_at = starts_at if starts_at is not None else self.starts_at
        new_ends_at = ends_at if ends_at is not None else self.ends_at
        Event._validate_period(new_starts_at, new_ends_at)

        if title is not None:
            Event._validate_title(title)
            self.title = title.strip()
        if description is not None:
            self.description = description or None
        if event_type is not None:
            Event._validate_event_type(event_type)
            self.event_type = event_type
        if status is not None:
            Event._validate_status(status)
            self.status = status
        if location is not None:
            self.location = location.strip() or None
        if responsible_user_id is not None:
            self.responsible_user_id = responsible_user_id
        self.starts_at = new_starts_at
        self.ends_at = new_ends_at
        if voter_id is not _UNSET:
            self.voter_id = voter_id
        if leadership_id is not _UNSET:
            self.leadership_id = leadership_id

        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)
