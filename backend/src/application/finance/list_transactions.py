from src.application.finance.dto import ListFinanceTransactionsInput, ListFinanceTransactionsOutput
from src.application.finance.mapper import summary_to_output, transaction_to_output
from src.domain.finance.repository import FinanceFilter, FinanceRepository

_MAX_PAGE_SIZE = 100


class ListFinanceTransactionsUseCase:
    def __init__(self, finance_repository: FinanceRepository) -> None:
        self._finance_repository = finance_repository

    async def execute(self, input_data: ListFinanceTransactionsInput) -> ListFinanceTransactionsOutput:
        page_size = min(max(input_data.page_size, 1), _MAX_PAGE_SIZE)
        page = max(input_data.page, 1)

        filters = FinanceFilter(
            type=input_data.type,
            category=input_data.category,
            occurred_after=input_data.occurred_after,
            occurred_before=input_data.occurred_before,
            include_deleted=False,
        )

        result = await self._finance_repository.list_paginated(input_data.tenant_id, filters, page, page_size)
        # O resumo aplica os MESMOS filtros da listagem (ex: se o usuário
        # filtrou por período, o saldo mostrado é o saldo daquele período,
        # não do histórico inteiro) — comportamento esperado de qualquer
        # relatório financeiro filtrável.
        summary = await self._finance_repository.get_summary(input_data.tenant_id, filters)

        return ListFinanceTransactionsOutput(
            items=[transaction_to_output(t) for t in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            total_pages=result.total_pages,
            summary=summary_to_output(summary),
        )
