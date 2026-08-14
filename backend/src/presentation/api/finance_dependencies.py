"""
Injeção de dependência (composition root) do módulo financeiro.
"""

from typing import Annotated

from fastapi import Depends

from src.application.finance.create_transaction import CreateFinanceTransactionUseCase
from src.application.finance.delete_transaction import DeleteFinanceTransactionUseCase
from src.application.finance.get_transaction import GetFinanceTransactionUseCase
from src.application.finance.list_transactions import ListFinanceTransactionsUseCase
from src.application.finance.update_transaction import UpdateFinanceTransactionUseCase
from src.infrastructure.database.repositories.finance_repository import SqlAlchemyFinanceRepository
from src.presentation.api.dependencies import DbSession


def get_finance_repository(session: DbSession) -> SqlAlchemyFinanceRepository:
    return SqlAlchemyFinanceRepository(session)


FinanceRepositoryDep = Annotated[SqlAlchemyFinanceRepository, Depends(get_finance_repository)]


def get_create_finance_transaction_use_case(
    finance_repository: FinanceRepositoryDep,
) -> CreateFinanceTransactionUseCase:
    return CreateFinanceTransactionUseCase(finance_repository)


def get_get_finance_transaction_use_case(
    finance_repository: FinanceRepositoryDep,
) -> GetFinanceTransactionUseCase:
    return GetFinanceTransactionUseCase(finance_repository)


def get_list_finance_transactions_use_case(
    finance_repository: FinanceRepositoryDep,
) -> ListFinanceTransactionsUseCase:
    return ListFinanceTransactionsUseCase(finance_repository)


def get_update_finance_transaction_use_case(
    finance_repository: FinanceRepositoryDep,
) -> UpdateFinanceTransactionUseCase:
    return UpdateFinanceTransactionUseCase(finance_repository)


def get_delete_finance_transaction_use_case(
    finance_repository: FinanceRepositoryDep,
) -> DeleteFinanceTransactionUseCase:
    return DeleteFinanceTransactionUseCase(finance_repository)
