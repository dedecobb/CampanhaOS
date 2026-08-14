from src.application.voters.dto import DeleteVoterInput
from src.application.voters.exceptions import VoterNotFoundError
from src.domain.voters.repository import VoterRepository


class DeleteVoterUseCase:
    def __init__(self, voter_repository: VoterRepository) -> None:
        self._voter_repository = voter_repository

    async def execute(self, input_data: DeleteVoterInput) -> None:
        voter = await self._voter_repository.find_by_id(input_data.tenant_id, input_data.voter_id)
        if voter is None or voter.is_deleted:
            raise VoterNotFoundError

        voter.soft_delete()
        await self._voter_repository.save(voter)
