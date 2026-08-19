from dataclasses import dataclass
from uuid import UUID

from src.domain.voters.repository import VoterRepository


@dataclass(frozen=True)
class GetLeadershipVoterCountsInput:
    tenant_id: UUID


class GetLeadershipVoterCountsUseCase:
    def __init__(self, voter_repository: VoterRepository) -> None:
        self._voter_repository = voter_repository

    async def execute(self, input_data: GetLeadershipVoterCountsInput) -> dict[UUID, int]:
        return await self._voter_repository.count_by_leadership(input_data.tenant_id)
