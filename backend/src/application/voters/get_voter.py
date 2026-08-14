from src.application.voters.dto import GetVoterInput, VoterOutput
from src.application.voters.exceptions import VoterNotFoundError
from src.application.voters.mapper import voter_to_output
from src.domain.voters.repository import VoterRepository


class GetVoterUseCase:
    def __init__(self, voter_repository: VoterRepository) -> None:
        self._voter_repository = voter_repository

    async def execute(self, input_data: GetVoterInput) -> VoterOutput:
        voter = await self._voter_repository.find_by_id(input_data.tenant_id, input_data.voter_id)
        if voter is None or voter.is_deleted:
            raise VoterNotFoundError
        return voter_to_output(voter)
