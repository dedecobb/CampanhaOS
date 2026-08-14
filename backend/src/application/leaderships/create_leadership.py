from src.application.leaderships.dto import CreateLeadershipInput, LeadershipOutput
from src.application.leaderships.mapper import leadership_to_output
from src.domain.leaderships.entities import Leadership
from src.domain.leaderships.repository import LeadershipRepository


class CreateLeadershipUseCase:
    def __init__(self, leadership_repository: LeadershipRepository) -> None:
        self._leadership_repository = leadership_repository

    async def execute(self, input_data: CreateLeadershipInput) -> LeadershipOutput:
        leadership = Leadership.create(
            tenant_id=input_data.tenant_id,
            created_by_user_id=input_data.created_by_user_id,
            name=input_data.name,
            influence_level=input_data.influence_level,
            region=input_data.region,
            estimated_votes=input_data.estimated_votes,
            team_size=input_data.team_size,
            notes=input_data.notes,
        )
        await self._leadership_repository.save(leadership)
        return leadership_to_output(leadership)
