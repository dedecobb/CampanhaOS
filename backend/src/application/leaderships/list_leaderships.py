from src.application.leaderships.dto import ListLeadershipsInput, ListLeadershipsOutput
from src.application.leaderships.mapper import leadership_to_output
from src.domain.leaderships.repository import LeadershipFilter, LeadershipRepository

_MAX_PAGE_SIZE = 100


class ListLeadershipsUseCase:
    def __init__(self, leadership_repository: LeadershipRepository) -> None:
        self._leadership_repository = leadership_repository

    async def execute(self, input_data: ListLeadershipsInput) -> ListLeadershipsOutput:
        page_size = min(max(input_data.page_size, 1), _MAX_PAGE_SIZE)
        page = max(input_data.page, 1)

        filters = LeadershipFilter(
            search_text=input_data.search_text,
            influence_level=input_data.influence_level,
            include_deleted=False,
        )
        result = await self._leadership_repository.list_paginated(
            input_data.tenant_id, filters, page, page_size
        )

        return ListLeadershipsOutput(
            items=[leadership_to_output(leadership) for leadership in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )
