from src.application.leaderships.dto import DeleteLeadershipInput
from src.application.leaderships.exceptions import LeadershipNotFoundError
from src.domain.leaderships.repository import LeadershipRepository


class DeleteLeadershipUseCase:
    def __init__(self, leadership_repository: LeadershipRepository) -> None:
        self._leadership_repository = leadership_repository

    async def execute(self, input_data: DeleteLeadershipInput) -> None:
        leadership = await self._leadership_repository.find_by_id(
            input_data.tenant_id, input_data.leadership_id
        )
        if leadership is None or leadership.is_deleted:
            raise LeadershipNotFoundError

        leadership.soft_delete()
        await self._leadership_repository.save(leadership)
