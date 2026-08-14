"""
Router de eventos (Agenda).

Mesma convenção dos routers anteriores: `current_user` sempre primeiro na
assinatura (ver comentário em v1/routers/voters.py).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.application.events.create_event import CreateEventUseCase
from src.application.events.delete_event import DeleteEventUseCase
from src.application.events.dto import (
    UNSET,
    CreateEventInput,
    DeleteEventInput,
    GetEventInput,
    ListEventsInput,
    UpdateEventInput,
)
from src.application.events.get_event import GetEventUseCase
from src.application.events.list_events import ListEventsUseCase
from src.application.events.update_event import UpdateEventUseCase
from src.presentation.api.dependencies import CurrentUser, DbSession
from src.presentation.api.events_dependencies import (
    get_create_event_use_case,
    get_delete_event_use_case,
    get_get_event_use_case,
    get_list_events_use_case,
    get_update_event_use_case,
)
from src.presentation.api.v1.schemas.events import (
    EventCreateRequest,
    EventListResponse,
    EventResponse,
    EventUpdateRequest,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    current_user: CurrentUser,
    request: EventCreateRequest,
    session: DbSession,
    use_case: Annotated[CreateEventUseCase, Depends(get_create_event_use_case)],
) -> EventResponse:
    output = await use_case.execute(
        CreateEventInput(
            tenant_id=current_user.tenant_id,
            created_by_user_id=current_user.id,
            # Se o request não especificar um responsável, assume o
            # próprio usuário autenticado.
            responsible_user_id=request.responsible_user_id or current_user.id,
            title=request.title,
            event_type=request.event_type,
            starts_at=request.starts_at,
            description=request.description,
            location=request.location,
            ends_at=request.ends_at,
            voter_id=request.voter_id,
            leadership_id=request.leadership_id,
        )
    )
    await session.commit()
    return EventResponse.model_validate(output)


@router.get("", response_model=EventListResponse)
async def list_events(
    current_user: CurrentUser,
    use_case: Annotated[ListEventsUseCase, Depends(get_list_events_use_case)],
    search: str | None = Query(None, description="Busca por título ou descrição"),
    event_type: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> EventListResponse:
    output = await use_case.execute(
        ListEventsInput(
            tenant_id=current_user.tenant_id,
            search_text=search,
            event_type=event_type,
            status=status_,
            page=page,
            page_size=page_size,
        )
    )
    return EventListResponse.model_validate(output)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    current_user: CurrentUser,
    use_case: Annotated[GetEventUseCase, Depends(get_get_event_use_case)],
) -> EventResponse:
    output = await use_case.execute(GetEventInput(tenant_id=current_user.tenant_id, event_id=event_id))
    return EventResponse.model_validate(output)


@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: UUID,
    current_user: CurrentUser,
    request: EventUpdateRequest,
    session: DbSession,
    use_case: Annotated[UpdateEventUseCase, Depends(get_update_event_use_case)],
) -> EventResponse:
    fields_set = request.model_fields_set
    voter_id = request.voter_id if "voter_id" in fields_set else UNSET
    leadership_id = request.leadership_id if "leadership_id" in fields_set else UNSET

    output = await use_case.execute(
        UpdateEventInput(
            tenant_id=current_user.tenant_id,
            event_id=event_id,
            title=request.title,
            description=request.description,
            event_type=request.event_type,
            status=request.status,
            location=request.location,
            starts_at=request.starts_at,
            ends_at=request.ends_at,
            responsible_user_id=request.responsible_user_id,
            voter_id=voter_id,
            leadership_id=leadership_id,
        )
    )
    await session.commit()
    return EventResponse.model_validate(output)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[DeleteEventUseCase, Depends(get_delete_event_use_case)],
) -> None:
    await use_case.execute(DeleteEventInput(tenant_id=current_user.tenant_id, event_id=event_id))
    await session.commit()
