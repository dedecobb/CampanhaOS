"""
Router de gestão de tenants (painel de super-admin).

Convenção: `current_admin: CurrentPlatformAdmin` sempre primeiro na
assinatura — mesmo espírito da convenção de `current_user` nos routers de
tenant, mas aqui é sobre garantir que TODA rota deste arquivo exige
autenticação de super-admin, nunca de usuário normal.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.application.admin.activate_tenant import ActivateTenantUseCase
from src.application.admin.dto import ActivateTenantInput, GetTenantInput, ListTenantsInput, SuspendTenantInput
from src.application.admin.get_tenant import GetTenantUseCase
from src.application.admin.list_tenants import ListTenantsUseCase
from src.application.admin.suspend_tenant import SuspendTenantUseCase
from src.presentation.api.admin_dependencies import (
    CurrentPlatformAdmin,
    get_activate_tenant_use_case,
    get_get_tenant_use_case,
    get_list_tenants_use_case,
    get_suspend_tenant_use_case,
)
from src.presentation.api.dependencies import DbSession
from src.presentation.api.v1.schemas.admin_tenants import TenantAdminListResponse, TenantAdminResponse

router = APIRouter(prefix="/admin/tenants", tags=["admin-tenants"])


@router.get("", response_model=TenantAdminListResponse)
async def list_tenants(
    current_admin: CurrentPlatformAdmin,
    use_case: Annotated[ListTenantsUseCase, Depends(get_list_tenants_use_case)],
    search: str | None = Query(None, description="Busca por nome da campanha"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> TenantAdminListResponse:
    output = await use_case.execute(ListTenantsInput(search_text=search, page=page, page_size=page_size))
    return TenantAdminListResponse.model_validate(output)


@router.get("/{tenant_id}", response_model=TenantAdminResponse)
async def get_tenant(
    tenant_id: UUID,
    current_admin: CurrentPlatformAdmin,
    use_case: Annotated[GetTenantUseCase, Depends(get_get_tenant_use_case)],
) -> TenantAdminResponse:
    output = await use_case.execute(GetTenantInput(tenant_id=tenant_id))
    return TenantAdminResponse.model_validate(output)


@router.post("/{tenant_id}/suspend", response_model=TenantAdminResponse)
async def suspend_tenant(
    tenant_id: UUID,
    current_admin: CurrentPlatformAdmin,
    session: DbSession,
    use_case: Annotated[SuspendTenantUseCase, Depends(get_suspend_tenant_use_case)],
) -> TenantAdminResponse:
    output = await use_case.execute(SuspendTenantInput(tenant_id=tenant_id))
    await session.commit()
    return TenantAdminResponse.model_validate(output)


@router.post("/{tenant_id}/activate", response_model=TenantAdminResponse)
async def activate_tenant(
    tenant_id: UUID,
    current_admin: CurrentPlatformAdmin,
    session: DbSession,
    use_case: Annotated[ActivateTenantUseCase, Depends(get_activate_tenant_use_case)],
) -> TenantAdminResponse:
    output = await use_case.execute(ActivateTenantInput(tenant_id=tenant_id))
    await session.commit()
    return TenantAdminResponse.model_validate(output)
