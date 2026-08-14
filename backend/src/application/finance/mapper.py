from src.application.finance.dto import FinanceSummaryOutput, FinanceTransactionOutput
from src.domain.finance.entities import FinanceTransaction
from src.domain.finance.repository import FinanceSummary


def transaction_to_output(transaction: FinanceTransaction) -> FinanceTransactionOutput:
    return FinanceTransactionOutput(
        id=transaction.id,
        created_by_user_id=transaction.created_by_user_id,
        type=transaction.type,
        category=transaction.category,
        amount=transaction.amount,
        description=transaction.description,
        occurred_at=transaction.occurred_at,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )


def summary_to_output(summary: FinanceSummary) -> FinanceSummaryOutput:
    return FinanceSummaryOutput(
        total_receitas=summary.total_receitas,
        total_despesas=summary.total_despesas,
        total_doacoes=summary.total_doacoes,
        saldo=summary.saldo,
    )
