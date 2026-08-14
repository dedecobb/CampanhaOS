from src.application.voters.dto import ListVotersInput, ListVotersOutput
from src.application.voters.mapper import voter_to_output
from src.domain.voters.repository import VoterFilter, VoterRepository

_MAX_PAGE_SIZE = 100


class ListVotersUseCase:
    def __init__(self, voter_repository: VoterRepository) -> None:
        self._voter_repository = voter_repository

    async def execute(self, input_data: ListVotersInput) -> ListVotersOutput:
        # Proteção contra page_size abusivo (ex: alguém pedindo 1 milhão de
        # linhas de uma vez) — regra de negócio do caso de uso, não do
        # schema Pydantic (que só valida formato/tipo).
        page_size = min(max(input_data.page_size, 1), _MAX_PAGE_SIZE)
        page = max(input_data.page, 1)

        filters = VoterFilter(
            search_text=input_data.search_text,
            tags=input_data.tags,
            include_deleted=False,
        )
        result = await self._voter_repository.list_paginated(
            input_data.tenant_id, filters, page, page_size
        )

        return ListVotersOutput(
            items=[voter_to_output(v) for v in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )
