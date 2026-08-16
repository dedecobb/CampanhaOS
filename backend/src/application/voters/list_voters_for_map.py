from src.application.voters.dto import ListVotersForMapInput, VoterMapPointOutput
from src.domain.voters.repository import VoterRepository


class ListVotersForMapUseCase:
    def __init__(self, voter_repository: VoterRepository) -> None:
        self._voter_repository = voter_repository

    async def execute(self, input_data: ListVotersForMapInput) -> list[VoterMapPointOutput]:
        voters = await self._voter_repository.list_with_coordinates(input_data.tenant_id)
        return [
            VoterMapPointOutput(
                id=voter.id,
                name=voter.name,
                address=voter.address,
                # Não-nulos garantidos pelo filtro do repository
                # (list_with_coordinates só retorna eleitores COM
                # coordenada) — o `# type: ignore` documenta essa garantia
                # de invariante, já que o domínio declara os campos como
                # opcionais (float | None) de forma geral.
                latitude=voter.latitude,  # type: ignore[arg-type]
                longitude=voter.longitude,  # type: ignore[arg-type]
            )
            for voter in voters
        ]
