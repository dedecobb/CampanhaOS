from src.application.finance.dto import CreateFinanceTransactionInput, FinanceTransactionOutput
from src.application.finance.mapper import transaction_to_output
from src.domain.finance.entities import FinanceTransaction
from src.domain.finance.repository import FinanceRepository


class CreateFinanceTransactionUseCase:
    def __init__(self, finance_repository: FinanceRepository) -> None:
        self._finance_repository = finance_repository

    async def execute(self, input_data: CreateFinanceTransactionInput) -> FinanceTransactionOutput:
        transaction = FinanceTransaction.create(
            tenant_id=input_data.tenant_id,
            created_by_user_id=input_data.created_by_user_id,
            type=input_data.type,
            category=input_data.category,
            amount=input_data.amount,
            occurred_at=input_data.occurred_at,
            description=input_data.description,
        )
        await self._finance_repository.save(transaction)
        return transaction_to_output(transaction)
