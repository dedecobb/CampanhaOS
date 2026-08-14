from src.application.finance.dto import FinanceTransactionOutput, GetFinanceTransactionInput
from src.application.finance.exceptions import FinanceTransactionNotFoundError
from src.application.finance.mapper import transaction_to_output
from src.domain.finance.repository import FinanceRepository


class GetFinanceTransactionUseCase:
    def __init__(self, finance_repository: FinanceRepository) -> None:
        self._finance_repository = finance_repository

    async def execute(self, input_data: GetFinanceTransactionInput) -> FinanceTransactionOutput:
        transaction = await self._finance_repository.find_by_id(
            input_data.tenant_id, input_data.transaction_id
        )
        if transaction is None or transaction.is_deleted:
            raise FinanceTransactionNotFoundError
        return transaction_to_output(transaction)
