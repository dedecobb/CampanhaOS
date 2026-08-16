"""
Configuração central do CampanhaOS.

Regra do projeto: nenhum outro módulo deve ler `os.environ` diretamente.
Toda configuração passa por esta classe `Settings`, que é validada na
inicialização da aplicação (fail-fast: se faltar uma variável obrigatória,
o app nem sobe).
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # ignora variáveis de ambiente não mapeadas aqui
    )

    # --- Aplicação ---
    app_name: str = "CampanhaOS API"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # --- Banco de dados ---
    # Formato esperado: postgresql+asyncpg://usuario:senha@host:porta/nome_do_banco
    # Usada pela APLICAÇÃO em runtime — deve apontar para um usuário SEM
    # privilégio de superusuário, senão o Row-Level Security (ADR-002) é
    # ignorado silenciosamente (superusuário do PostgreSQL sempre ignora
    # RLS, mesmo com FORCE ROW LEVEL SECURITY — isso não é configurável).
    database_url: str = Field(..., description="URL de conexão async do PostgreSQL (usuário de aplicação, sem superuser)")
    # Usada SÓ pelo Alembic para rodar migrações — precisa de privilégios
    # elevados para criar tabelas, políticas de RLS, roles, etc. Nunca usada
    # pela aplicação em runtime.
    migration_database_url: str = Field(..., description="URL de conexão do PostgreSQL com privilégios de migração (superuser)")
    database_echo_sql: bool = False  # True apenas para debug local de queries

    # --- Redis (cache + broker do Celery) ---
    redis_url: str = Field(..., description="URL de conexão do Redis")

    # --- Autenticação (usado a partir do Módulo 1) ---
    jwt_secret_key: str = Field(..., description="Chave secreta para assinar tokens JWT")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # --- Observabilidade ---
    sentry_dsn: str | None = None

    # --- CORS (produção) ---
    # URL do frontend em produção — usada para liberar CORS. Em dev,
    # continuamos usando localhost:5173 hardcoded (ver main.py). Sem essa
    # variável configurada em produção, o CORS ficaria fechado para
    # qualquer origem — bug real que existia desde o Módulo 0 e só foi
    # percebido agora, ao planejar o deploy de verdade.
    frontend_url: str | None = None

    # --- Geocodificação ---
    # Opcional de propósito: se não configurado, a geocodificação
    # automática de endereço de eleitor simplesmente não acontece (sem
    # quebrar a criação/edição do eleitor) — ver GeocodingService.
    mapbox_access_token: str | None = None

    # --- WhatsApp (Twilio) ---
    # Todos opcionais — sem eles, as rotas de WhatsApp simplesmente
    # retornam erro claro em vez de derrubar a aplicação inteira.
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_whatsapp_from_number: str | None = None  # formato "whatsapp:+14155238886"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Retorna a instância única (singleton) de Settings.

    `lru_cache` garante que o arquivo `.env` só é lido uma vez, não a cada
    request — importante para performance, já que Settings pode ser usado
    como dependência do FastAPI em várias rotas.
    """
    return Settings()  # type: ignore[call-arg]
