from src.application.events.dto import DeleteEventInput
from src.application.events.exceptions import EventNotFoundError
from src.domain.events.repository import EventRepository


class DeleteEventUseCase:
    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repository = event_repository

    async def execute(self, input_data: DeleteEventInput) -> None:
        event = await self._event_repository.find_by_id(input_data.tenant_id, input_data.event_id)
        if event is None or event.is_deleted:
            raise EventNotFoundError

        event.soft_delete()
        await self._event_repository.save(event)
