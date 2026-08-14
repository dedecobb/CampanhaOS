# syntax=docker/dockerfile:1

# ---- Stage 1: builder ----
# Instala dependências num ambiente isolado, incluindo ferramentas de
# compilação que NÃO precisam ir para a imagem final (ex: gcc para libs
# nativas como asyncpg/bcrypt).
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

# ---- Stage 2: runtime ----
# Imagem final: só o necessário para RODAR a aplicação, sem compiladores.
FROM python:3.12-slim AS runtime

WORKDIR /app

# Usuário não-root: rodar containers como root é uma prática de segurança
# desaconselhada (se o processo for comprometido, o atacante herda menos
# privilégios dentro do container).
RUN addgroup --system app && adduser --system --ingroup app app

# Copia as dependências já instaladas do stage anterior (não reinstala nada).
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY ./src ./src
COPY ./alembic ./alembic
COPY ./scripts ./scripts
COPY pyproject.toml alembic.ini ./

RUN chown -R app:app /app
USER app

EXPOSE 8000

# --proxy-headers: necessário porque em produção o backend fica atrás do
# NGINX (ADR-005) — sem essa flag, o FastAPI não enxerga corretamente o IP
# real do cliente nem se a conexão original era HTTPS.
CMD ["uvicorn", "src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

# ---- Stage 3: dev ----
# Usado pelo docker-compose local (ver docker-compose.yml, target: dev).
# Adiciona pytest/ruff/mypy/httpx por cima da imagem de runtime, mantendo
# a imagem de PRODUÇÃO (stage "runtime", usada no deploy real) enxuta e
# sem ferramentas de desenvolvimento que ela nunca deveria expor.
FROM runtime AS dev

USER root
COPY ./tests ./tests
RUN pip install --no-cache-dir ".[dev]"
USER app
