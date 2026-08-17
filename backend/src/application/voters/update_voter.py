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

        # Detecta ANTES de aplicar a atualização se algum dos 5 campos que
        # afetam a geocodificação está sendo alterado nesta chamada —
        # precisa ser feito antes de `update_details`, ou perderíamos a
        # informação de "o que mudou nesta chamada" (depois de aplicado,
        # os valores novo e antigo ficam indistinguíveis).
        address_fields_changed = any(
            field is not None
            for field in (
                input_data.address,
                input_data.city,
                input_data.state,
                input_data.postal_code,
                input_data.neighborhood,
            )
        )

        voter.update_details(
            name=input_data.name,
            phone=input_data.phone,
            address=input_data.address,
            city=input_data.city,
            state=input_data.state,
            postal_code=input_data.postal_code,
            neighborhood=input_data.neighborhood,
            gender=input_data.gender,
            birth_date=input_data.birth_date,
            # Só aplica coordenada manual aqui — a automática (geocodificada)
            # é setada depois, abaixo, usando os campos já atualizados.
            latitude=input_data.latitude,
            longitude=input_data.longitude,
            tags=input_data.tags,
            custom_fields=input_data.custom_fields,
            notes=input_data.notes,
            **leadership_kwargs,
        )

        # Re-geocodifica automaticamente só se algum campo de endereço
        # mudou NESTA chamada e nenhuma coordenada manual veio junto —
        # evita geocodificar de novo em todo PATCH que não mexe em
        # endereço/cidade/estado/CEP/bairro (ex: só atualizando o telefone).
        # Campos passados SEPARADOS — ver GeocodingService.geocode.
        if address_fields_changed and input_data.latitude is None and input_data.longitude is None:
            if voter.has_geocodable_address:
                coordinates = await self._geocoding_service.geocode(
                    address_line=voter.address,  # type: ignore[arg-type]
                    city=voter.city,
                    state=voter.state,
                    postal_code=voter.postal_code,
                    neighborhood=voter.neighborhood,
                )
                if coordinates is not None:
                    voter.latitude = coordinates.latitude
                    voter.longitude = coordinates.longitude

        await self._voter_repository.save(voter)
        return voter_to_output(voter)
