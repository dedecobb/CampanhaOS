"""
Router de health check.

Endpoint simples usado por: load balancers, Docker healthcheck, Kubernetes
liveness/readiness probes e monitoramento (Prometheus/Grafana) para saber
se a aplicação está no ar. Não deve conter lógica de negócio.
"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """
    Retorna 200 OK se a aplicação está rodando.

    Nota de evolução: quando o Módulo 1 (banco de dados) existir, este
    endpoint deve ser expandido para também checar a conexão com o
    PostgreSQL e o Redis (um "readiness check" de verdade), mantendo este
    endpoint simples como "liveness check" separado.
    """
    return {"status": "ok"}
