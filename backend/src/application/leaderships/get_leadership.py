from src.application.leaderships.dto import GetLeadershipInput, LeadershipOutput
from src.application.leaderships.exceptions import LeadershipNotFoundError
from src.application.leaderships.mapper import leadership_to_output
from src.domain.leaderships.repository import LeadershipRepository


class GetLeadershipUseCase:
    def __init__(self, leadership_repository: LeadershipRepository) -> None:
        self._leadership_repository = leadership_repository

    async def execute(self, input_data: GetLeadershipInput) -> LeadershipOutput:
        leadership = await self._leadership_repository.find_by_id(
            input_data.tenant_id, input_data.leadership_id
        )
        if leadership is None or leadership.is_deleted:
            raise LeadershipNotFoundError
        return leadership_to_output(leadership)
