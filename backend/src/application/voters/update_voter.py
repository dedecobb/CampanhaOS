from src.application.geocoding.ports import GeocodingService
from src.application.leaderships.exceptions import LeadershipNotFoundError
from src.application.voters.dto import UNSET, UpdateVoterInput, VoterOutput
from src.application.voters.exceptions import VoterNotFoundError
from src.application.voters.mapper import voter_to_output
from src.domain.leaderships.repository import LeadershipRepository
from src.domain.voters.repository import VoterRepository


class UpdateVoterUseCase:
    def __init__(
        self,
        voter_repository: VoterRepository,
        leadership_repository: LeadershipRepository,
        geocoding_service: GeocodingService,
    ) -> None:
        self._voter_repository = voter_repository
        self._leadership_repository = leadership_repository
        self._geocoding_service = geocoding_service

    async def execute(self, input_data: UpdateVoterInput) -> VoterOutput:
        voter = await self._voter_repository.find_by_id(input_data.tenant_id, input_data.voter_id)
        if voter is None or voter.is_deleted:
            raise VoterNotFoundError

        # `leadership_id` usa o sentinela UNSET (ver dto.py): só entra no
        # dicionário de kwargs se foi de fato informado no request — se
        # não foi (UNSET), nem passamos o argumento para
        # `update_details()`, e o próprio domínio mantém o valor atual
        # (mesmo mecanismo de sentinela, replicado nesta camada).
        leadership_kwargs = {}
        if input_data.leadership_id is not UNSET:
            if input_data.leadership_id is not None:
                exists = await self._leadership_repository.exists(
                    input_data.tenant_id, input_data.leadership_id
                )
                if not exists:
                    raise LeadershipNotFoundError
            leadership_kwargs["leadership_id"] = input_data.leadership_id

        latitude = input_data.latitude
        longitude = input_data.longitude
        # Re-geocodifica automaticamente só se o endereço está sendo
        # alterado NESTA chamada e nenhuma coordenada manual veio junto
        # — evita geocodificar de novo em todo PATCH que não mexe no
        # endereço (ex: só atualizando o telefone).
        if input_data.address and latitude is None and longitude is None:
            coordinates = await self._geocoding_service.geocode(input_data.address)
            if coordinates is not None:
                latitude = coordinates.latitude
                longitude = coordinates.longitude

        voter.update_details(
            name=input_data.name,
            phone=input_data.phone,
            address=input_data.address,
            latitude=latitude,
            longitude=longitude,
            tags=input_data.tags,
            custom_fields=input_data.custom_fields,
            notes=input_data.notes,
            **leadership_kwargs,
        )
        await self._voter_repository.save(voter)
        return voter_to_output(voter)
