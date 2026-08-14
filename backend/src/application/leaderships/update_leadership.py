from src.application.leaderships.dto import LeadershipOutput, UpdateLeadershipInput
from src.application.leaderships.exceptions import LeadershipNotFoundError
from src.application.leaderships.mapper import leadership_to_output
from src.domain.leaderships.repository import LeadershipRepository


class UpdateLeadershipUseCase:
    def __init__(self, leadership_repository: LeadershipRepository) -> None:
        self._leadership_repository = leadership_repository

    async def execute(self, input_data: UpdateLeadershipInput) -> LeadershipOutput:
        leadership = await self._leadership_repository.find_by_id(
            input_data.tenant_id, input_data.leadership_id
        )
        if leadership is None or leadership.is_deleted:
            raise LeadershipNotFoundError

        leadership.update_details(
            name=input_data.name,
            region=input_data.region,
            estimated_votes=input_data.estimated_votes,
            influence_level=input_data.influence_level,
            team_size=input_data.team_size,
            notes=input_data.notes,
        )
        await self._leadership_repository.save(leadership)
        return leadership_to_output(leadership)
