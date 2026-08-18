from dataclasses import dataclass
from uuid import UUID

from src.application.finance.exceptions import FinanceTransactionNotFoundError, NoAttachmentError
from src.application.shared.file_storage_port import FileStoragePort
from src.domain.finance.repository import FinanceRepository


@dataclass(frozen=True)
class RemoveFinanceAttachmentInput:
    tenant_id: UUID
    transaction_id: UUID


class RemoveFinanceAttachmentUseCase:
    def __init__(self, finance_repository: FinanceRepository, file_storage: FileStoragePort) -> None:
        self._finance_repository = finance_repository
        self._file_storage = file_storage

    async def execute(self, input_data: RemoveFinanceAttachmentInput) -> None:
        transaction = await self._finance_repository.find_by_id(input_data.tenant_id, input_data.transaction_id)
        if transaction is None or transaction.is_deleted:
            raise FinanceTransactionNotFoundError

        if transaction.attachment_storage_key is None:
            raise NoAttachmentError

        storage_key = transaction.attachment_storage_key
        transaction.remove_attachment()
        await self._finance_repository.save(transaction)

        # Remove do R2 só DEPOIS de confirmar que a remoção da referência
        # foi salva — mesma lógica de ordem do upload, invertida: aqui
        # queremos que o banco "esqueça" o anexo antes de apagar o
        # arquivo de verdade, não o contrário.
        await self._file_storage.delete(storage_key)
