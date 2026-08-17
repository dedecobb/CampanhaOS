"""
Caso de uso do autocadastro público — a pessoa cadastra a SI MESMA,
sem login, através de um link com token (ver Tenant.generate_registration_token,
domínio de tenants).
"""

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from src.application.geocoding.ports import GeocodingService
from src.application.shared.exceptions import ApplicationError
from src.application.shared.rate_limiter_port import RateLimiter
from src.application.tenant_settings.exceptions import (
    InvalidRegistrationTokenError,
    RegistrationRateLimitExceededError,
)
from src.application.voters.dto import VoterOutput
from src.application.voters.mapper import voter_to_output
from src.domain.tenants.repository import TenantRepository
from src.domain.voters.entities import Voter
from src.domain.voters.repository import VoterRepository

# Limites conservadores de propósito: o uso esperado é UMA pessoa se
# cadastrando UMA vez a partir do próprio celular — não uma campanha
# cadastrando várias pessoas de um único IP (isso já existe, é o CRUD
# autenticado normal). Números baixos aqui protegem contra bot sem
# incomodar o uso legítimo.
_MAX_REGISTRATIONS_PER_IP_PER_HOUR = 3
_RATE_LIMIT_WINDOW_SECONDS = 3600

SetTenantContextCallable = Callable[[UUID], Awaitable[None]]


@dataclass(frozen=True)
class PublicSelfRegisterVoterInput:
    registration_token: str
    client_ip: str
    name: str
    consent_given: bool
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    neighborhood: str | None = None
    gender: str | None = None
    birth_date: date | None = None


class ConsentNotGivenError(ApplicationError):
    """
    Levantada se `consent_given=False` chegar até o caso de uso — não
    deveria acontecer no fluxo normal (o frontend obriga marcar a
    casinha antes de habilitar o envio), mas alguém chamando a API
    diretamente, pulando o frontend, poderia tentar enviar sem
    consentimento. Herda de ApplicationError para ser mapeada num status
    HTTP claro (422), não um 500 genérico não tratado.
    """

    def __init__(self) -> None:
        super().__init__("É necessário confirmar o consentimento para se cadastrar")


class PublicSelfRegisterVoterUseCase:
    def __init__(
        self,
        tenant_repository: TenantRepository,
        voter_repository: VoterRepository,
        geocoding_service: GeocodingService,
        rate_limiter: RateLimiter,
        set_tenant_context: SetTenantContextCallable,
    ) -> None:
        self._tenant_repository = tenant_repository
        self._voter_repository = voter_repository
        self._geocoding_service = geocoding_service
        self._rate_limiter = rate_limiter
        self._set_tenant_context = set_tenant_context

    async def execute(self, input_data: PublicSelfRegisterVoterInput) -> VoterOutput:
        if not input_data.consent_given:
            raise ConsentNotGivenError

        tenant = await self._tenant_repository.find_by_registration_token(input_data.registration_token)
        if tenant is None:
            raise InvalidRegistrationTokenError

        # Limite por IP + token combinados — mesmo IP em campanhas
        # diferentes tem cotas independentes; mesmo IP na MESMA campanha
        # compartilha a cota (evita um único bot esgotar via múltiplos
        # tokens, se algum dia isso fizer sentido testar).
        rate_limit_key = f"public_registration:{tenant.id}:{input_data.client_ip}"
        is_allowed = await self._rate_limiter.check_and_consume(
            rate_limit_key,
            max_per_window=_MAX_REGISTRATIONS_PER_IP_PER_HOUR,
            window_seconds=_RATE_LIMIT_WINDOW_SECONDS,
        )
        if not is_allowed:
            raise RegistrationRateLimitExceededError

        # `voters` tem RLS — como não há CurrentUser aqui (endpoint
        # público), ninguém declarou o contexto de tenant ainda. Mesmo
        # padrão já usado no webhook do WhatsApp.
        await self._set_tenant_context(tenant.id)

        voter = Voter.create(
            tenant_id=tenant.id,
            created_by_user_id=None,  # autocadastro — ninguém da equipe criou
            name=input_data.name,
            # Base legal sempre "consentimento" aqui, nunca outra coisa —
            # é literalmente a pessoa concordando em fornecer o próprio
            # dado, o caso mais direto de consentimento que existe.
            legal_basis="consentimento",
            phone=input_data.phone,
            address=input_data.address,
            city=input_data.city,
            state=input_data.state,
            postal_code=input_data.postal_code,
            neighborhood=input_data.neighborhood,
            gender=input_data.gender,
            birth_date=input_data.birth_date,
        )

        if voter.has_geocodable_address:
            coordinates = await self._geocoding_service.geocode(
                address_line=voter.address,  # type: ignore[arg-type]
                city=voter.city,
                state=voter.state,
                postal_code=voter.postal_code,
                neighborhood=voter.neighborhood,
            )
            if coordinates is not None:
                voter.latitude = coordinates.latitude
                voter.longitude = coordinates.longitude

        await self._voter_repository.save(voter)
        return voter_to_output(voter)
