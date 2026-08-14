"""
Handlers globais de exceção.

Por que centralizar aqui em vez de try/except em cada router: com dezenas
de endpoints planejados para os próximos módulos, repetir tratamento de
erro em cada um seria duplicação e, mais cedo ou tarde, alguém esqueceria
de tratar um caso. Registrando os handlers uma vez no `main.py`, TODO
endpoint automaticamente ganha esse comportamento consistente.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from src.application.admin.exceptions import InvalidAdminCredentialsError
from src.application.admin.exceptions import TenantNotFoundError as AdminTenantNotFoundError
from src.application.auth.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    TenantNotAuthenticatableError,
    WeakPasswordError,
)
from src.application.billing.exceptions import InactivePlanError, PlanNotFoundError
from src.application.events.exceptions import EventNotFoundError, ResponsibleUserNotFoundError
from src.application.finance.exceptions import FinanceTransactionNotFoundError
from src.application.leaderships.exceptions import LeadershipNotFoundError
from src.application.shared.exceptions import ApplicationError
from src.application.voters.exceptions import VoterNotFoundError
from src.domain.shared.exceptions import DomainError

# Mapeamento explícito de tipo de exceção -> status HTTP. Qualquer
# ApplicationError não listado aqui cai no default (400) do handler.
_APPLICATION_ERROR_STATUS_MAP: dict[type[ApplicationError], int] = {
    InvalidCredentialsError: status.HTTP_401_UNAUTHORIZED,
    InvalidTokenError: status.HTTP_401_UNAUTHORIZED,
    TenantNotAuthenticatableError: status.HTTP_403_FORBIDDEN,
    EmailAlreadyExistsError: status.HTTP_409_CONFLICT,
    WeakPasswordError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    VoterNotFoundError: status.HTTP_404_NOT_FOUND,
    LeadershipNotFoundError: status.HTTP_404_NOT_FOUND,
    EventNotFoundError: status.HTTP_404_NOT_FOUND,
    ResponsibleUserNotFoundError: status.HTTP_404_NOT_FOUND,
    FinanceTransactionNotFoundError: status.HTTP_404_NOT_FOUND,
    InvalidAdminCredentialsError: status.HTTP_401_UNAUTHORIZED,
    AdminTenantNotFoundError: status.HTTP_404_NOT_FOUND,
    PlanNotFoundError: status.HTTP_404_NOT_FOUND,
    InactivePlanError: status.HTTP_409_CONFLICT,
}


async def application_error_handler(request: Request, exc: ApplicationError) -> JSONResponse:
    status_code = _APPLICATION_ERROR_STATUS_MAP.get(type(exc), status.HTTP_400_BAD_REQUEST)
    return JSONResponse(status_code=status_code, content={"detail": str(exc)})


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    # Violação de regra de negócio da entidade (ex: nome vazio, e-mail
    # malformado) — tratamos como 422 (entidade não processável), mesma
    # semântica que o FastAPI já usa para erro de validação do Pydantic.
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, content={"detail": str(exc)})
