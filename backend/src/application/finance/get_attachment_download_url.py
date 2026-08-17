from dataclasses import dataclass
from uuid import UUID

from src.application.finance.exceptions import FinanceTransactionNotFoundError, NoAttachmentError
from src.application.shared.file_storage_port import FileStoragePort
from src.domain.finance.repository import FinanceRepository


@dataclass(frozen=True)
class GetFinanceAttachmentDownloadUrlInput:
    tenant_id: UUID
    transaction_id: UUID


@dataclass(frozen=True)
class GetFinanceAttachmentDownloadUrlOutput:
    download_url: str
    filename: str


class GetFinanceAttachmentDownloadUrlUseCase:
    def __init__(self, finance_repository: FinanceRepository, file_storage: FileStoragePort) -> None:
        self._finance_repository = finance_repository
        self._file_storage = file_storage

    async def execute(
        self, input_data: GetFinanceAttachmentDownloadUrlInput
    ) -> GetFinanceAttachmentDownloadUrlOutput:
        transaction = await self._finance_repository.find_by_id(input_data.tenant_id, input_data.transaction_id)
        if transaction is None or transaction.is_deleted:
            raise FinanceTransactionNotFoundError

        if transaction.attachment_storage_key is None or transaction.attachment_filename is None:
            raise NoAttachmentError

        download_url = await self._file_storage.generate_download_url(transaction.attachment_storage_key)
        return GetFinanceAttachmentDownloadUrlOutput(
            download_url=download_url, filename=transaction.attachment_filename
        )
