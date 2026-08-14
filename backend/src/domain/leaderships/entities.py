"""
Entidade de domínio: Leadership (Liderança).

RF-05 (Fase 1): pessoa com influência numa região, que ajuda a mobilizar
eleitores para a campanha. `estimated_votes` é uma estimativa que o
próprio usuário da campanha informa (não é calculado pelo sistema).
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from src.domain.shared.exceptions import DomainError, InvalidNameError

_VALID_INFLUENCE_LEVELS = frozenset({"baixa", "media", "alta"})


class InvalidInfluenceLevelError(DomainError):
    def __init__(self, value: str) -> None:
        super().__init__(
            f"Nível de influência '{value}' inválido. Valores aceitos: {', '.join(sorted(_VALID_INFLUENCE_LEVELS))}"
        )


class InvalidEstimatedVotesError(DomainError):
    def __init__(self) -> None:
        super().__init__("Estimativa de votos não pode ser negativa")


class InvalidTeamSizeError(DomainError):
    def __init__(self) -> None:
        super().__init__("Tamanho de equipe não pode ser negativo")


@dataclass
class Leadership:
    id: UUID
    tenant_id: UUID
    created_by_user_id: UUID
    name: str
    region: str | None
    estimated_votes: int
    influence_level: str
    team_size: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None

    @staticmethod
    def create(
        tenant_id: UUID,
        created_by_user_id: UUID,
        name: str,
        influence_level: str,
        region: str | None = None,
        estimated_votes: int = 0,
        team_size: int | None = None,
        notes: str | None = None,
    ) -> "Leadership":
        Leadership._validate_name(name)
        Leadership._validate_influence_level(influence_level)
        Leadership._validate_estimated_votes(estimated_votes)
        Leadership._validate_team_size(team_size)

        now = datetime.now(UTC)
        return Leadership(
            id=uuid4(),
            tenant_id=tenant_id,
            created_by_user_id=created_by_user_id,
            name=name.strip(),
            region=region.strip() if region else None,
            estimated_votes=estimated_votes,
            influence_level=influence_level,
            team_size=team_size,
            notes=notes,
            created_at=now,
            updated_at=now,
            deleted_at=None,
        )

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise InvalidNameError("Nome da liderança não pode ser vazio")

    @staticmethod
    def _validate_influence_level(influence_level: str) -> None:
        if influence_level not in _VALID_INFLUENCE_LEVELS:
            raise InvalidInfluenceLevelError(influence_level)

    @staticmethod
    def _validate_estimated_votes(estimated_votes: int) -> None:
        if estimated_votes < 0:
            raise InvalidEstimatedVotesError

    @staticmethod
    def _validate_team_size(team_size: int | None) -> None:
        if team_size is not None and team_size < 0:
            raise InvalidTeamSizeError

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def update_details(
        self,
        *,
        name: str | None = None,
        region: str | None = None,
        estimated_votes: int | None = None,
        influence_level: str | None = None,
        team_size: int | None = None,
        notes: str | None = None,
    ) -> None:
        if name is not None:
            Leadership._validate_name(name)
            self.name = name.strip()
        if region is not None:
            self.region = region.strip() or None
        if estimated_votes is not None:
            Leadership._validate_estimated_votes(estimated_votes)
            self.estimated_votes = estimated_votes
        if influence_level is not None:
            Leadership._validate_influence_level(influence_level)
            self.influence_level = influence_level
        if team_size is not None:
            Leadership._validate_team_size(team_size)
            self.team_size = team_size
        if notes is not None:
            self.notes = notes or None

        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)
