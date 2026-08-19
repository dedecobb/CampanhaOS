"""
Router de lideranças.

Mesma convenção do router de eleitores: `current_user` sempre primeiro na
assinatura (ver comentário detalhado em v1/routers/voters.py).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.application.leaderships.create_leadership import CreateLeadershipUseCase
from src.application.leaderships.delete_leadership import DeleteLeadershipUseCase
from src.application.leaderships.dto import (
    CreateLeadershipInput,
    DeleteLeadershipInput,
    GetLeadershipInput,
    ListLeadershipsInput,
    UpdateLeadershipInput,
)
from src.application.leaderships.get_leadership import GetLeadershipUseCase
from src.application.leaderships.get_voter_counts import GetLeadershipVoterCountsInput, GetLeadershipVoterCountsUseCase
from src.application.leaderships.list_leaderships import ListLeadershipsUseCase
from src.application.leaderships.update_leadership import UpdateLeadershipUseCase
from src.presentation.api.dependencies import CurrentUser, DbSession
from src.presentation.api.leaderships_dependencies import (
    get_create_leadership_use_case,
    get_delete_leadership_use_case,
    get_get_leadership_use_case,
    get_leadership_voter_counts_use_case,
    get_list_leaderships_use_case,
    get_update_leadership_use_case,
)
from src.presentation.api.v1.schemas.leaderships import (
    LeadershipCreateRequest,
    LeadershipListResponse,
    LeadershipResponse,
    LeadershipUpdateRequest,
    LeadershipVoterCountsResponse,
)

router = APIRouter(prefix="/leaderships", tags=["leaderships"])


@router.post("", response_model=LeadershipResponse, status_code=status.HTTP_201_CREATED)
async def create_leadership(
    current_user: CurrentUser,
    request: LeadershipCreateRequest,
    session: DbSession,
    use_case: Annotated[CreateLeadershipUseCase, Depends(get_create_leadership_use_case)],
) -> LeadershipResponse:
    output = await use_case.execute(
        CreateLeadershipInput(
            tenant_id=current_user.tenant_id,
            created_by_user_id=current_user.id,
            name=request.name,
            influence_level=request.influence_level,
            region=request.region,
            estimated_votes=request.estimated_votes,
            team_size=request.team_size,
            notes=request.notes,
        )
    )
    await session.commit()
    return LeadershipResponse.model_validate(output)


@router.get("", response_model=LeadershipListResponse)
async def list_leaderships(
    current_user: CurrentUser,
    use_case: Annotated[ListLeadershipsUseCase, Depends(get_list_leaderships_use_case)],
    search: str | None = Query(None, description="Busca por nome ou região"),
    influence_level: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> LeadershipListResponse:
    output = await use_case.execute(
        ListLeadershipsInput(
            tenant_id=current_user.tenant_id,
            search_text=search,
            influence_level=influence_level,
            page=page,
            page_size=page_size,
        )
    )
    return LeadershipListResponse.model_validate(output)


@router.get("/voter-counts", response_model=LeadershipVoterCountsResponse)
async def get_leadership_voter_counts(
    current_user: CurrentUser,
    use_case: Annotated[GetLeadershipVoterCountsUseCase, Depends(get_leadership_voter_counts_use_case)],
) -> LeadershipVoterCountsResponse:
    """
    IMPORTANTE: precisa vir ANTES de `/{leadership_id}` neste arquivo —
    o FastAPI casa rotas na ordem declarada, e `/{leadership_id}`
    tentaria capturar "voter-counts" como se fosse um id (mesma lição já
    documentada em `voters.py`, rota `/map`).
    """
    counts = await use_case.execute(GetLeadershipVoterCountsInput(tenant_id=current_user.tenant_id))
    return LeadershipVoterCountsResponse(counts={str(leadership_id): count for leadership_id, count in counts.items()})


@router.get("/{leadership_id}", response_model=LeadershipResponse)
async def get_leadership(
    leadership_id: UUID,
    current_user: CurrentUser,
    use_case: Annotated[GetLeadershipUseCase, Depends(get_get_leadership_use_case)],
) -> LeadershipResponse:
    output = await use_case.execute(
        GetLeadershipInput(tenant_id=current_user.tenant_id, leadership_id=leadership_id)
    )
    return LeadershipResponse.model_validate(output)


@router.patch("/{leadership_id}", response_model=LeadershipResponse)
async def update_leadership(
    leadership_id: UUID,
    current_user: CurrentUser,
    request: LeadershipUpdateRequest,
    session: DbSession,
    use_case: Annotated[UpdateLeadershipUseCase, Depends(get_update_leadership_use_case)],
) -> LeadershipResponse:
    output = await use_case.execute(
        UpdateLeadershipInput(
            tenant_id=current_user.tenant_id,
            leadership_id=leadership_id,
            name=request.name,
            region=request.region,
            estimated_votes=request.estimated_votes,
            influence_level=request.influence_level,
            team_size=request.team_size,
            notes=request.notes,
        )
    )
    await session.commit()
    return LeadershipResponse.model_validate(output)


@router.delete("/{leadership_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_leadership(
    leadership_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[DeleteLeadershipUseCase, Depends(get_delete_leadership_use_case)],
) -> None:
    await use_case.execute(
        DeleteLeadershipInput(tenant_id=current_user.tenant_id, leadership_id=leadership_id)
    )
    await session.commit()
