from src.application.events.dto import ListEventsInput, ListEventsOutput
from src.application.events.mapper import event_to_output
from src.domain.events.repository import EventFilter, EventRepository

_MAX_PAGE_SIZE = 100


class ListEventsUseCase:
    def __init__(self, event_repository: EventRepository) -> None:
        self._event_repository = event_repository

    async def execute(self, input_data: ListEventsInput) -> ListEventsOutput:
        page_size = min(max(input_data.page_size, 1), _MAX_PAGE_SIZE)
        page = max(input_data.page, 1)

        filters = EventFilter(
            search_text=input_data.search_text,
            event_type=input_data.event_type,
            status=input_data.status,
            starts_after=input_data.starts_after,
            starts_before=input_data.starts_before,
            include_deleted=False,
        )
        result = await self._event_repository.list_paginated(input_data.tenant_id, filters, page, page_size)

        return ListEventsOutput(
            items=[event_to_output(event) for event in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )
