"""
Caso de uso: enviar (ou substituir) o anexo de um lançamento financeiro.
"""

import uuid
from dataclasses import dataclass
from uuid import UUID

from src.application.finance.exceptions import (
    FinanceTransactionNotFoundError,
    UnsupportedFileTypeError,
)
from src.application.shared.exceptions import ApplicationError
from src.application.shared.file_storage_port import FileStoragePort
from src.domain.finance.entities import MAX_ATTACHMENT_SIZE_BYTES
from src.domain.finance.repository import FinanceRepository
from src.infrastructure.storage.file_signature import detect_content_type

_EXTENSION_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/pdf": ".pdf",
}


class AttachmentTooLargeError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(
            f"Arquivo muito grande — limite de {MAX_ATTACHMENT_SIZE_BYTES / 1024 / 1024:.0f}MB"
        )


@dataclass(frozen=True)
class UploadFinanceAttachmentInput:
    tenant_id: UUID
    transaction_id: UUID
    filename: str
    file_bytes: bytes


class UploadFinanceAttachmentUseCase:
    def __init__(self, finance_repository: FinanceRepository, file_storage: FileStoragePort) -> None:
        self._finance_repository = finance_repository
        self._file_storage = file_storage

    async def execute(self, input_data: UploadFinanceAttachmentInput) -> None:
        # >>> DIAGNÓSTICO TEMPORÁRIO — remover depois de resolver o 404 <<<
        print(
            f">>> [DIAGNÓSTICO UPLOAD] Buscando transação — tenant_id={input_data.tenant_id!r}, "
            f"transaction_id={input_data.transaction_id!r}",
            flush=True,
        )
        transaction = await self._finance_repository.find_by_id(input_data.tenant_id, input_data.transaction_id)
        print(
            f">>> [DIAGNÓSTICO UPLOAD] Resultado: transaction={'ENCONTRADA' if transaction else 'None'}"
            + (f", is_deleted={transaction.is_deleted}" if transaction else ""),
            flush=True,
        )
        if transaction is None or transaction.is_deleted:
            raise FinanceTransactionNotFoundError

        # Validação de TAMANHO acontece ANTES de qualquer upload — sem
        # isso, um arquivo grande demais subiria pro R2 à toa (gastando
        # armazenamento e banda) só pra ser rejeitado alguns milissegundos
        # depois, na validação de domínio dentro de attach_document().
        if len(input_data.file_bytes) > MAX_ATTACHMENT_SIZE_BYTES:
            raise AttachmentTooLargeError

        # Detecta o tipo real pelo CONTEÚDO do arquivo — nunca confia no
        # nome/extensão enviado (ver file_signature.py). Também validado
        # ANTES do upload, mesmo motivo.
        real_content_type = detect_content_type(input_data.file_bytes)
        if real_content_type is None:
            raise UnsupportedFileTypeError

        extension = _EXTENSION_BY_CONTENT_TYPE[real_content_type]
        storage_key = (
            f"finance-attachments/{input_data.tenant_id}/{input_data.transaction_id}/{uuid.uuid4()}{extension}"
        )

        # Guarda a chave antiga ANTES de sobrescrever — se já havia um
        # anexo, apagamos o arquivo velho do R2 só DEPOIS de confirmar
        # que o novo subiu e foi salvo com sucesso (ordem importa: nunca
        # apagar o antigo antes de garantir que o novo está seguro).
        previous_storage_key = transaction.attachment_storage_key

        await self._file_storage.upload(storage_key, input_data.file_bytes, real_content_type)

        transaction.attach_document(
            storage_key=storage_key,
            filename=input_data.filename,
            content_type=real_content_type,
            size_bytes=len(input_data.file_bytes),
        )
        await self._finance_repository.save(transaction)

        if previous_storage_key:
            await self._file_storage.delete(previous_storage_key)
