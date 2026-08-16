"""
Router de eleitores (CRM).

CONVENÇÃO IMPORTANTE deste router (e de todo router futuro que toque
tabela com RLS): `current_user: CurrentUser` é sempre o PRIMEIRO parâmetro
de cada função de endpoint. O FastAPI resolve dependências na ordem em
que aparecem na assinatura — isso garante que `get_current_user` (que
declara o contexto de tenant na sessão do banco, ver Módulo 1) já rodou
antes de qualquer dependência que toque a tabela `voters` (que tem RLS).
Inverter essa ordem pode fazer uma query rodar sem o contexto de tenant
setado, e a policy de RLS bloquear tudo (fail-closed) — ou, pior, alguma
mudança futura no mecanismo passar batido sem esse cuidado.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.application.voters.create_voter import CreateVoterUseCase
from src.application.voters.delete_voter import DeleteVoterUseCase
from src.application.voters.dto import (
    UNSET,
    CreateVoterInput,
    DeleteVoterInput,
    GetVoterInput,
    ListVotersForMapInput,
    ListVotersInput,
    UpdateVoterInput,
)
from src.application.voters.get_voter import GetVoterUseCase
from src.application.voters.list_voters import ListVotersUseCase
from src.application.voters.list_voters_for_map import ListVotersForMapUseCase
from src.application.voters.update_voter import UpdateVoterUseCase
from src.presentation.api.dependencies import CurrentUser, DbSession
from src.presentation.api.v1.schemas.voters import (
    VoterCreateRequest,
    VoterListResponse,
    VoterMapPointResponse,
    VoterResponse,
    VoterUpdateRequest,
)
from src.presentation.api.voters_dependencies import (
    get_create_voter_use_case,
    get_delete_voter_use_case,
    get_get_voter_use_case,
    get_list_voters_for_map_use_case,
    get_list_voters_use_case,
    get_update_voter_use_case,
)

router = APIRouter(prefix="/voters", tags=["voters"])


@router.post("", response_model=VoterResponse, status_code=status.HTTP_201_CREATED)
async def create_voter(
    current_user: CurrentUser,
    request: VoterCreateRequest,
    session: DbSession,
    use_case: Annotated[CreateVoterUseCase, Depends(get_create_voter_use_case)],
) -> VoterResponse:
    output = await use_case.execute(
        CreateVoterInput(
            tenant_id=current_user.tenant_id,
            created_by_user_id=current_user.id,
            name=request.name,
            legal_basis=request.legal_basis,
            phone=request.phone,
            address=request.address,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            latitude=request.latitude,
            longitude=request.longitude,
            tags=request.tags,
            custom_fields=request.custom_fields,
            notes=request.notes,
            leadership_id=request.leadership_id,
        )
    )
    await session.commit()
    return VoterResponse.model_validate(output)


@router.get("", response_model=VoterListResponse)
async def list_voters(
    current_user: CurrentUser,
    use_case: Annotated[ListVotersUseCase, Depends(get_list_voters_use_case)],
    search: str | None = Query(None, description="Busca por nome ou telefone"),
    tags: list[str] | None = Query(None, description="Eleitor precisa ter todas as tags listadas"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> VoterListResponse:
    output = await use_case.execute(
        ListVotersInput(
            tenant_id=current_user.tenant_id,
            search_text=search,
            tags=tags,
            page=page,
            page_size=page_size,
        )
    )
    return VoterListResponse.model_validate(output)


@router.get("/map", response_model=list[VoterMapPointResponse])
async def list_voters_for_map(
    current_user: CurrentUser,
    use_case: Annotated[ListVotersForMapUseCase, Depends(get_list_voters_for_map_use_case)],
) -> list[VoterMapPointResponse]:
    """
    IMPORTANTE: esta rota precisa vir ANTES de `/{voter_id}` no arquivo —
    o FastAPI casa rotas na ordem em que são declaradas, e `/{voter_id}`
    (UUID) tentaria capturar "map" como se fosse um id, dando 422 em vez
    de rodar este endpoint.
    """
    outputs = await use_case.execute(ListVotersForMapInput(tenant_id=current_user.tenant_id))
    return [VoterMapPointResponse.model_validate(o) for o in outputs]


@router.get("/{voter_id}", response_model=VoterResponse)
async def get_voter(
    voter_id: UUID,
    current_user: CurrentUser,
    use_case: Annotated[GetVoterUseCase, Depends(get_get_voter_use_case)],
) -> VoterResponse:
    output = await use_case.execute(GetVoterInput(tenant_id=current_user.tenant_id, voter_id=voter_id))
    return VoterResponse.model_validate(output)


@router.patch("/{voter_id}", response_model=VoterResponse)
async def update_voter(
    voter_id: UUID,
    current_user: CurrentUser,
    request: VoterUpdateRequest,
    session: DbSession,
    use_case: Annotated[UpdateVoterUseCase, Depends(get_update_voter_use_case)],
) -> VoterResponse:
    # `leadership_id` é o único campo com semântica de 3 estados: "não veio
    # no JSON" (preservar associação atual), "veio como null" (remover
    # associação) ou "veio com um id" (trocar associação). Os outros
    # campos deste request usam `None` só como "não alterar" — aqui
    # precisamos checar `model_fields_set` para diferenciar de verdade.
    leadership_id = request.leadership_id if "leadership_id" in request.model_fields_set else UNSET

    output = await use_case.execute(
        UpdateVoterInput(
            tenant_id=current_user.tenant_id,
            voter_id=voter_id,
            name=request.name,
            phone=request.phone,
            address=request.address,
            city=request.city,
            state=request.state,
            postal_code=request.postal_code,
            latitude=request.latitude,
            longitude=request.longitude,
            tags=request.tags,
            custom_fields=request.custom_fields,
            notes=request.notes,
            leadership_id=leadership_id,
        )
    )
    await session.commit()
    return VoterResponse.model_validate(output)


@router.delete("/{voter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voter(
    voter_id: UUID,
    current_user: CurrentUser,
    session: DbSession,
    use_case: Annotated[DeleteVoterUseCase, Depends(get_delete_voter_use_case)],
) -> None:
    await use_case.execute(DeleteVoterInput(tenant_id=current_user.tenant_id, voter_id=voter_id))
    await session.commit()
