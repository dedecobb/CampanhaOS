from src.application.admin.dto import TenantAdminOutput
from src.domain.tenants.entities import Tenant


def tenant_to_admin_output(tenant: Tenant) -> TenantAdminOutput:
    return TenantAdminOutput(
        id=tenant.id,
        name=tenant.name,
        status=tenant.status.value,
        created_at=tenant.created_at,
    )