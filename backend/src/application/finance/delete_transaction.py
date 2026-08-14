from src.application.finance.dto import DeleteFinanceTransactionInput
from src.application.finance.exceptions import FinanceTransactionNotFoundError
from src.domain.finance.repository import FinanceRepository


class DeleteFinanceTransactionUseCase:
    def __init__(self, finance_repository: FinanceRepository) -> None:
        self._finance_repository = finance_repository

    async def execute(self, input_data: DeleteFinanceTransactionInput) -> None:
        transaction = await self._finance_repository.find_by_id(
            input_data.tenant_id, input_data.transaction_id
        )
        if transaction is None or transaction.is_deleted:
            raise FinanceTransactionNotFoundError

        transaction.soft_delete()
        await self._finance_repository.save(transaction)
