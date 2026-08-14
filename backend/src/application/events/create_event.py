from src.application.events.dto import CreateEventInput, EventOutput
from src.application.events.exceptions import ResponsibleUserNotFoundError
from src.application.events.mapper import event_to_output
from src.application.leaderships.exceptions import LeadershipNotFoundError
from src.application.voters.exceptions import VoterNotFoundError
from src.domain.events.entities import Event
from src.domain.events.repository import EventRepository
from src.domain.leaderships.repository import LeadershipRepository
from src.domain.users.repository import UserRepository
from src.domain.voters.repository import VoterRepository


class CreateEventUseCase:
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

    async def execute(self, input_data: CreateEventInput) -> EventOutput:
        responsible = await self._user_repository.find_by_id(
            input_data.tenant_id, input_data.responsible_user_id
        )
        if responsible is None:
            raise ResponsibleUserNotFoundError

        if input_data.voter_id is not None:
            voter = await self._voter_repository.find_by_id(input_data.tenant_id, input_data.voter_id)
            if voter is None or voter.is_deleted:
                raise VoterNotFoundError

        if input_data.leadership_id is not None:
            exists = await self._leadership_repository.exists(input_data.tenant_id, input_data.leadership_id)
            if not exists:
                raise LeadershipNotFoundError

        event = Event.create(
            tenant_id=input_data.tenant_id,
            created_by_user_id=input_data.created_by_user_id,
            responsible_user_id=input_data.responsible_user_id,
            title=input_data.title,
            event_type=input_data.event_type,
            starts_at=input_data.starts_at,
            description=input_data.description,
            location=input_data.location,
            ends_at=input_data.ends_at,
            voter_id=input_data.voter_id,
            leadership_id=input_data.leadership_id,
        )
        await self._event_repository.save(event)
        return event_to_output(event)
