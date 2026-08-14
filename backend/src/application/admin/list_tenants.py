from src.application.admin.dto import ListTenantsInput, ListTenantsOutput
from src.application.admin.mapper import tenant_to_admin_output
from src.domain.tenants.repository import TenantFilter, TenantRepository

_MAX_PAGE_SIZE = 100


class ListTenantsUseCase:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self._tenant_repository = tenant_repository

    async def execute(self, input_data: ListTenantsInput) -> ListTenantsOutput:
        page_size = min(max(input_data.page_size, 1), _MAX_PAGE_SIZE)
        page = max(input_data.page, 1)

        filters = TenantFilter(search_text=input_data.search_text)
        result = await self._tenant_repository.list_paginated(filters, page, page_size)

        return ListTenantsOutput(
            items=[tenant_to_admin_output(t) for t in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
        )
