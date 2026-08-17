"""
Injeção de dependência (composition root) do módulo financeiro.
"""

from typing import Annotated

from fastapi import Depends

from src.application.finance.create_transaction import CreateFinanceTransactionUseCase
from src.application.finance.delete_transaction import DeleteFinanceTransactionUseCase
from src.application.finance.get_attachment_download_url import GetFinanceAttachmentDownloadUrlUseCase
from src.application.finance.get_transaction import GetFinanceTransactionUseCase
from src.application.finance.list_transactions import ListFinanceTransactionsUseCase
from src.application.finance.remove_attachment import RemoveFinanceAttachmentUseCase
from src.application.finance.update_transaction import UpdateFinanceTransactionUseCase
from src.application.finance.upload_attachment import UploadFinanceAttachmentUseCase
from src.application.shared.file_storage_port import FileStoragePort
from src.config.settings import Settings, get_settings
from src.infrastructure.database.repositories.finance_repository import SqlAlchemyFinanceRepository
from src.infrastructure.storage.cloudflare_r2_storage import CloudflareR2Storage
from src.presentation.api.dependencies import DbSession


def get_finance_repository(session: DbSession) -> SqlAlchemyFinanceRepository:
    return SqlAlchemyFinanceRepository(session)


def get_file_storage(settings: Annotated[Settings, Depends(get_settings)]) -> FileStoragePort:
    # Mesmo espírito de get_geocoding_service/get_whatsapp_sender: se as
    # credenciais não estiverem configuradas, ainda construímos o objeto
    # (com strings vazias) — a falha acontece na hora de tentar usar de
    # verdade, com erro claro, não na inicialização da aplicação.
    return CloudflareR2Storage(
        account_id=settings.cloudflare_account_id or "",
        access_key_id=settings.cloudflare_r2_access_key_id or "",
        secret_access_key=settings.cloudflare_r2_secret_access_key or "",
        bucket_name=settings.cloudflare_r2_bucket_name or "",
    )


FinanceRepositoryDep = Annotated[SqlAlchemyFinanceRepository, Depends(get_finance_repository)]
FileStorageDep = Annotated[FileStoragePort, Depends(get_file_storage)]


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


def get_upload_finance_attachment_use_case(
    finance_repository: FinanceRepositoryDep,
    file_storage: FileStorageDep,
) -> UploadFinanceAttachmentUseCase:
    return UploadFinanceAttachmentUseCase(finance_repository, file_storage)


def get_remove_finance_attachment_use_case(
    finance_repository: FinanceRepositoryDep,
    file_storage: FileStorageDep,
) -> RemoveFinanceAttachmentUseCase:
    return RemoveFinanceAttachmentUseCase(finance_repository, file_storage)


def get_finance_attachment_download_url_use_case(
    finance_repository: FinanceRepositoryDep,
    file_storage: FileStorageDep,
) -> GetFinanceAttachmentDownloadUrlUseCase:
    return GetFinanceAttachmentDownloadUrlUseCase(finance_repository, file_storage)
