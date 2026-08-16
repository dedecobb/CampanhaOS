"""
Ponto de entrada da aplicação CampanhaOS API.

Este arquivo é intencionalmente "burro": não contém regra de negócio.
Ele apenas monta o app FastAPI, registra middlewares globais e inclui os
routers de cada versão da API. Toda lógica real vive em `application/` e
`domain/`; os routers em `presentation/api/v1/routers/` apenas traduzem
HTTP <-> casos de uso.
"""

print(">>> [DIAGNÓSTICO] Iniciando carregamento de main.py...", flush=True)

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

print(">>> [DIAGNÓSTICO] Imports de terceiros OK, importando módulos do projeto...", flush=True)

from src.application.auth.exceptions import ApplicationError
from src.config.settings import get_settings
from src.domain.shared.exceptions import DomainError
from src.presentation.api.error_handlers import application_error_handler, domain_error_handler
from src.presentation.api.v1.routers import (
    admin_auth,
    admin_billing,
    admin_tenants,
    auth,
    events,
    finance,
    health,
    leaderships,
    voters,
    whatsapp,
)

print(">>> [DIAGNÓSTICO] Todos os imports OK. Carregando Settings...", flush=True)
settings = get_settings()
print(">>> [DIAGNÓSTICO] Settings carregado. Ambiente:", settings.environment, flush=True)

# Sentry: só inicializa se um DSN de verdade estiver configurado — em
# desenvolvimento local, SENTRY_DSN fica vazio no .env.example de
# propósito, então isso não faz nada localmente, sem custo nenhum.
if settings.sentry_dsn:
    print(">>> [DIAGNÓSTICO] Inicializando Sentry...", flush=True)
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        # Amostragem de traces de performance — 100% seria caro/exagerado
        # em produção de grande porte; para o volume esperado do piloto
        # (1-2 tenants), 100% ainda é barato e dá visibilidade completa.
        # Ajustar para baixo (ex: 0.1) se o volume de tráfego crescer.
        traces_sample_rate=1.0,
    )
else:
    print(">>> [DIAGNÓSTICO] SENTRY_DSN não configurado, pulando Sentry.", flush=True)

print(">>> [DIAGNÓSTICO] Criando instância do FastAPI...", flush=True)

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url=f"{settings.api_v1_prefix}/docs",
    openapi_url=f"{settings.api_v1_prefix}/openapi.json",
)

# CORS: em desenvolvimento, libera localhost:5173 (porta padrão do Vite).
# Em produção, lê de settings.frontend_url — se não estiver configurada,
# fica fechado (fail-closed, mesmo espírito do RLS: prefiro bloquear tudo
# a liberar tudo por engano).
if settings.is_production:
    _allowed_origins = [settings.frontend_url] if settings.frontend_url else []
else:
    _allowed_origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(ApplicationError, application_error_handler)
app.add_exception_handler(DomainError, domain_error_handler)

app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(voters.router, prefix=settings.api_v1_prefix)
app.include_router(leaderships.router, prefix=settings.api_v1_prefix)
app.include_router(events.router, prefix=settings.api_v1_prefix)
app.include_router(finance.router, prefix=settings.api_v1_prefix)
app.include_router(admin_auth.router, prefix=settings.api_v1_prefix)
app.include_router(admin_tenants.router, prefix=settings.api_v1_prefix)
app.include_router(admin_billing.router, prefix=settings.api_v1_prefix)
app.include_router(whatsapp.router, prefix=settings.api_v1_prefix)

print(">>> [DIAGNÓSTICO] main.py carregado com sucesso, app FastAPI pronto.", flush=True)
