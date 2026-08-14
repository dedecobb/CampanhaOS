# CampanhaOS

SaaS multi-tenant para gestão de campanhas eleitorais (vereador a governador/senador): CRM de eleitores, lideranças, agenda, financeiro, jurídico, pesquisas, IA generativa/RAG e comunicação via WhatsApp oficial.

> 📖 Antes de contribuir com qualquer código, leia `docs/PROJETO-FONTE-DA-VERDADE.md` — é a fonte oficial de decisões técnicas do projeto. Nenhum código deve contradizer o que está registrado lá.

## Arquitetura

- **Backend:** Python 3.12 / FastAPI / SQLAlchemy 2.0 (async) / PostgreSQL / Redis / Celery
- **Frontend:** React / TypeScript / Vite / TailwindCSS / Shadcn UI *(a partir do Módulo 5)*
- **Estilo:** Clean Architecture + DDD tático + Hexagonal (Ports & Adapters), monólito modular
- **Multi-tenancy:** schema compartilhado + `tenant_id` + Row-Level Security do PostgreSQL

Detalhes completos: `docs/fase-1-requisitos-arquitetura.md`.

## Como rodar localmente

### Pré-requisitos

- Docker e Docker Compose instalados
- Git

### Passos

1. Clone o repositório e entre na pasta:
   ```bash
   git clone <url-do-repositorio>
   cd campanhaos
   ```

2. Copie o arquivo de variáveis de ambiente e ajuste os valores (principalmente `JWT_SECRET_KEY` — veja o comentário dentro do arquivo para gerar uma chave forte):
   ```bash
   cp .env.example .env
   ```

3. Suba os serviços:
   ```bash
   docker compose up --build
   ```

4. Verifique se a API está no ar:
   ```bash
   curl http://localhost:8000/api/v1/health
   # Esperado: {"status":"ok"}
   ```

5. Documentação interativa da API (Swagger):
   ```
   http://localhost:8000/api/v1/docs
   ```

6. Interface de inspeção do banco (Adminer, apenas desenvolvimento):
   ```
   http://localhost:8081
   ```
   (Sistema: PostgreSQL · Servidor: `postgres` · usuário/senha/banco: os definidos no seu `.env`)

## Rodando testes e lint localmente (fora do Docker)

> Nota: dentro do Docker, `DATABASE_URL`/`REDIS_URL` usam os nomes dos serviços (`postgres`, `redis`) como host. Rodando pytest/ruff diretamente na sua máquina (fora da rede do Docker), use `localhost`, já que o `docker-compose.yml` expõe as portas 5432/6379 no host.

```bash
# Suba só os serviços de apoio (deixe o backend em si rodar direto na sua máquina):
docker compose up -d postgres redis

cd backend
pip install -e ".[dev]"
ruff check .
mypy src

export DATABASE_URL=postgresql+asyncpg://campanhaos_app:troque_esta_outra_senha_localmente@localhost:5432/campanhaos
export MIGRATION_DATABASE_URL=postgresql+asyncpg://campanhaos:troque_esta_senha_localmente@localhost:5432/campanhaos
export APP_DB_PASSWORD=troque_esta_outra_senha_localmente
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET_KEY=qualquer_valor_para_teste_local

alembic upgrade head
pytest --cov=src --cov-report=term-missing
```

## Estrutura do projeto

```
.
├── backend/            # API (Clean Architecture: domain/application/infrastructure/presentation)
├── frontend/           # SPA React (a partir do Módulo 5)
├── docs/               # Documentos de decisão e requisitos do projeto
├── docker-compose.yml
└── .env.example
```

## Status do projeto

Ver tabela de módulos em `docs/PROJETO-FONTE-DA-VERDADE.md`, seção "Mapa de Módulos do Sistema".
