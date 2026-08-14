from src.application.events.dto import UNSET, EventOutput, UpdateEventInput
from src.application.events.exceptions import EventNotFoundError, ResponsibleUserNotFoundError
from src.application.events.mapper import event_to_output
from src.application.leaderships.exceptions import LeadershipNotFoundError
from src.application.voters.exceptions import VoterNotFoundError
from src.domain.events.repository import EventRepository
from src.domain.leaderships.repository import LeadershipRepository
from src.domain.users.repository import UserRepository
from src.domain.voters.repository import VoterRepository


class UpdateEventUseCase:
    def __init__(
        self,
        event_repository: EventRepository,
        user_repository: UserRepository,
        voter_repository: VoterRepository,
        leadership_repository: LeadershipRepository,
    ) -> None:
        self._event_repository = event_repository
        self._user_repository = user_repository
        self._voter_repository = voter_repository
        self._leadership_repository = leadership_repository

    async def execute(self, input_data: UpdateEventInput) -> EventOutput:
        event = await self._event_repository.find_by_id(input_data.tenant_id, input_data.event_id)
        if event is None or event.is_deleted:
            raise EventNotFoundError

        if input_data.responsible_user_id is not None:
            responsible = await self._user_repository.find_by_id(
                input_data.tenant_id, input_data.responsible_user_id
            )
            if responsible is None:
                raise ResponsibleUserNotFoundError

        # Mesmo padrão de sentinela do Módulo 3: só entra no dicionário de
        # kwargs (e só é validado) se foi de fato informado no request.
        association_kwargs = {}

        if input_data.voter_id is not UNSET:
            if input_data.voter_id is not None:
                voter = await self._voter_repository.find_by_id(input_data.tenant_id, input_data.voter_id)
                if voter is None or voter.is_deleted:
                    raise VoterNotFoundError
            association_kwargs["voter_id"] = input_data.voter_id

        if input_data.leadership_id is not UNSET:
            if input_data.leadership_id is not None:
                exists = await self._leadership_repository.exists(
                    input_data.tenant_id, input_data.leadership_id
                )
                if not exists:
                    raise LeadershipNotFoundError
            association_kwargs["leadership_id"] = input_data.leadership_id

        event.update_details(
            title=input_data.title,
            description=input_data.description,
            event_type=input_data.event_type,
            status=input_data.status,
            location=input_data.location,
            starts_at=input_data.starts_at,
            ends_at=input_data.ends_at,
            responsible_user_id=input_data.responsible_user_id,
            **association_kwargs,
        )
        await self._event_repository.save(event)
        return event_to_output(event)
