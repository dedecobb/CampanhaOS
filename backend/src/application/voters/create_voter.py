from src.application.geocoding.ports import GeocodingService
from src.application.leaderships.exceptions import LeadershipNotFoundError
from src.application.voters.dto import CreateVoterInput, VoterOutput
from src.application.voters.mapper import voter_to_output
from src.domain.leaderships.repository import LeadershipRepository
from src.domain.voters.entities import Voter
from src.domain.voters.repository import VoterRepository


class CreateVoterUseCase:
    def __init__(
        self,
        voter_repository: VoterRepository,
        leadership_repository: LeadershipRepository,
        geocoding_service: GeocodingService,
    ) -> None:
        self._voter_repository = voter_repository
        self._leadership_repository = leadership_repository
        self._geocoding_service = geocoding_service

    async def execute(self, input_data: CreateVoterInput) -> VoterOutput:
        if input_data.leadership_id is not None:
            exists = await self._leadership_repository.exists(
                input_data.tenant_id, input_data.leadership_id
            )
            if not exists:
                raise LeadershipNotFoundError

        voter = Voter.create(
            tenant_id=input_data.tenant_id,
            created_by_user_id=input_data.created_by_user_id,
            name=input_data.name,
            legal_basis=input_data.legal_basis,
            phone=input_data.phone,
            address=input_data.address,
            city=input_data.city,
            state=input_data.state,
            postal_code=input_data.postal_code,
            latitude=input_data.latitude,
            longitude=input_data.longitude,
            tags=input_data.tags,
            custom_fields=input_data.custom_fields,
            notes=input_data.notes,
            leadership_id=input_data.leadership_id,
        )

        # Só geocodifica automaticamente se houver o que geocodificar E
        # nenhuma coordenada manual foi passada — respeita quem prefere
        # fornecer a coordenada exata na mão. `geocoding_query` combina
        # endereço + cidade + estado + CEP (ver Voter, domínio) — muito
        # mais preciso do que geocodificar só o endereço isolado.
        if voter.geocoding_query and voter.latitude is None and voter.longitude is None:
            coordinates = await self._geocoding_service.geocode(voter.geocoding_query)
            if coordinates is not None:
                voter.latitude = coordinates.latitude
                voter.longitude = coordinates.longitude

        await self._voter_repository.save(voter)
        return voter_to_output(voter)
