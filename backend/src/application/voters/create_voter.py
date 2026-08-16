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

        latitude = input_data.latitude
        longitude = input_data.longitude
        # Só geocodifica automaticamente se um endereço foi informado E
        # nenhuma coordenada manual foi passada — respeita quem prefere
        # fornecer a coordenada exata na mão (ex: importação de dado que
        # já vem geocodificado de outra fonte).
        if input_data.address and latitude is None and longitude is None:
            coordinates = await self._geocoding_service.geocode(input_data.address)
            if coordinates is not None:
                latitude = coordinates.latitude
                longitude = coordinates.longitude

        voter = Voter.create(
            tenant_id=input_data.tenant_id,
            created_by_user_id=input_data.created_by_user_id,
            name=input_data.name,
            legal_basis=input_data.legal_basis,
            phone=input_data.phone,
            address=input_data.address,
            latitude=latitude,
            longitude=longitude,
            tags=input_data.tags,
            custom_fields=input_data.custom_fields,
            notes=input_data.notes,
            leadership_id=input_data.leadership_id,
        )
        await self._voter_repository.save(voter)
        return voter_to_output(voter)
