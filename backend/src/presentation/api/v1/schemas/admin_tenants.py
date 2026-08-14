from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TenantAdminResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    status: str
    created_at: datetime


class TenantAdminListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[TenantAdminResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
