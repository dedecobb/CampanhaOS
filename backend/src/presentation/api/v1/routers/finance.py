"""
Router financeiro (Financeiro básico).

Mesma convenção dos routers anteriores: `current_user` sempre primeiro na
assinatura (ver comentário em v1/routers/voters.py).
"""

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from src.application.finance.create_transaction import CreateFinanceTransactionUseCase
from src.application.finance.delete_transaction import DeleteFinanceTransactionUseCase
from src.application.finance.dto import (
    CreateFinanceTransactionInput,
    DeleteFinanceTransactionInput,
    GetFinanceTransactionInput,
    ListFinanceTransactionsInput,
    UpdateFinanceTransactionInput,
)
from src.application.finance.get_attachment_download_url import (
    GetFinanceAttachmentDownloadUrlInput,
    GetFinanceAttachmentDownloadUrlUseCase,
)
from src.application.finance.get_transaction import GetFinanceTransactionUseCase
from src.application.finance.list_transactions import ListFinanceTransactionsUseCase
from src.application.finance.remove_attachment import RemoveFinanceAttachmentInput, RemoveFinanceAttachmentUseCase
from src.application.finance.update_transaction import UpdateFinanceTransactionUseCase
from src.application.finance.upload_attachment import UploadFinanceAttachmentInput, UploadFinanceAttachmentUseCase
from src.presentation.api.dependencies import CurrentUser, DbSession
from src.presentation.api.finance_dependencies import (
    get_create_finance_transaction_use_case,
    get_delete_finance_transaction_use_case,
    get_finance_attachment_download_url_use_case,
    get_get_finance_transaction_use_case,
    get_list_finance_transactions_use_case,
    get_remove_finance_attachment_use_case,
    get_update_finance_transaction_use_case,
    get_upload_finance_attachment_use_case,
)
from src.presentation.api.v1.schemas.finance import (
    FinanceAttachmentDownloadResponse,
    FinanceTransactionCreateRequest,
    FinanceTransactionListResponse,
    FinanceTransactionResponse,
    FinanceTransactionUpdateRequest,
)

router = APIRouter(prefix="/finance", tags=["finance"])


@router.post("", response_model=FinanceTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    current_user: CurrentUser,
    request: FinanceTransactionCreateRequest,
    session: DbSession,
    use_case: Annotated[CreateFinanceTransactionUseCase, Depends(get_create_finance_transaction_use_case)],
) -> FinanceTransactionResponse:
    output = await use_case.execute(
        CreateFinanceTransactionInput(
            tenant_id=current_user.tenant_id,
            created_by_user_id=current_user.id,
            type=request.type,
            category=request.category,
            amount=request.amount,
            occurred_at=request.occurred_at,
            description=request.description,
        )
    )
    await session.commit()
    return FinanceTransactionResponse.model_validate(output)


@router.get("", response_model=FinanceTransactionListResponse)
async def list_transactions(
    current_user: CurrentUser,
    use_case: Annotated[ListFinanceTransactionsUseCase, Depends(get_list_finance_transactions_use_case)],
    type: str | None = Query(None),  # nome mais natural pro cliente da API do que "type_"
    category: str | None = Query(None),
    occurred_after: date | None = Query(None),
    occurred_before: date | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> FinanceTransactionListResponse:
    output = await use_case.execute(
        ListFinanceTransactionsInput(
            tenant_id=current_user.tenant_id,
            type=type,
            category=category,
            occurred_after=occurred_after,
            occurred_before=occurred_before,
            page=page,
            page_size=page_size,
        )
    )
    return FinanceTransactionListResponse.model_validate(output)


@router.get("/{transaction_id}", response_model=FinanceTransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: CurrentUser,
    use_case: Annotated[GetFinanceTransactionUseCase, Depends(get_get_finance_transaction_use_case)],
) -> FinanceTransactionResponse:
    output = await use_case.execute(
        GetFinanceTransactionInput(tenant_id=current_user.tenant_id, transaction_id=transaction_id)
    )
    return FinanceTransactionResponse.model_validate(output)


@router.patch("/{transaction_id}", response_model=FinanceTransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    current_user: CurrentUser,
    request: FinanceTransactionUpdateRequest,
    session: DbSession,
    use_case: Annotated[UpdateFinanceTransactionUseCase, Depends(get_update_finance_transaction_use_case)],
) -> FinanceTransactionResponse:
    output = await use_case.execute(
        UpdateFinanceTransactionInput(
            tenant_id=current_user.tenant_id,
            transaction_id=transaction_id,
            type=request.type,
            category=request.category,
            amount=request.amount,
            occurred_at=request.occurred_at,
            description=request.description,
        )
    )
    await session.commit()
    return FinanceTransactionResponse.model_validate(output)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[DeleteFinanceTransactionUseCase, Depends(get_delete_finance_transaction_use_case)],
) -> None:
    await use_case.execute(
        DeleteFinanceTransactionInput(tenant_id=current_user.tenant_id, transaction_id=transaction_id)
    )
    await session.commit()


@router.post("/{transaction_id}/attachment", response_model=FinanceTransactionResponse)
async def upload_attachment(
    transaction_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[UploadFinanceAttachmentUseCase, Depends(get_upload_finance_attachment_use_case)],
    get_use_case: Annotated[GetFinanceTransactionUseCase, Depends(get_get_finance_transaction_use_case)],
    file: UploadFile = File(...),
) -> FinanceTransactionResponse:
    file_bytes = await file.read()
    # >>> DIAGNÓSTICO TEMPORÁRIO — remover depois de resolver o 404 <<<
    print(
        f">>> [DIAGNÓSTICO ROUTER] transaction_id (da URL)={transaction_id!r}, "
        f"current_user.tenant_id={current_user.tenant_id!r}, "
        f"file.filename={file.filename!r}, tamanho={len(file_bytes)} bytes",
        flush=True,
    )
    await use_case.execute(
        UploadFinanceAttachmentInput(
            tenant_id=current_user.tenant_id,
            transaction_id=transaction_id,
            filename=file.filename or "arquivo",
            file_bytes=file_bytes,
        )
    )
    await session.commit()
    # Retorna o lançamento já atualizado — evita o frontend precisar de
    # uma segunda chamada só pra ver o anexo refletido.
    output = await get_use_case.execute(
        GetFinanceTransactionInput(tenant_id=current_user.tenant_id, transaction_id=transaction_id)
    )
    return FinanceTransactionResponse.model_validate(output)


@router.delete("/{transaction_id}/attachment", status_code=status.HTTP_204_NO_CONTENT)
async def remove_attachment(
    transaction_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[RemoveFinanceAttachmentUseCase, Depends(get_remove_finance_attachment_use_case)],
) -> None:
    await use_case.execute(
        RemoveFinanceAttachmentInput(tenant_id=current_user.tenant_id, transaction_id=transaction_id)
    )
    await session.commit()


@router.get("/{transaction_id}/attachment/download-url", response_model=FinanceAttachmentDownloadResponse)
async def get_attachment_download_url(
    transaction_id: UUID,
    current_user: CurrentUser,
    use_case: Annotated[
        GetFinanceAttachmentDownloadUrlUseCase, Depends(get_finance_attachment_download_url_use_case)
    ],
) -> FinanceAttachmentDownloadResponse:
    output = await use_case.execute(
        GetFinanceAttachmentDownloadUrlInput(tenant_id=current_user.tenant_id, transaction_id=transaction_id)
    )
    return FinanceAttachmentDownloadResponse(download_url=output.download_url, filename=output.filename)
