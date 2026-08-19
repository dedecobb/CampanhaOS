# CampanhaOS — Fonte da Verdade do Projeto

**Última atualização:** 18/08/2026
**Fase atual:** Fase 2 em andamento
**Módulo em desenvolvimento:** nenhum (Link de Cadastro por Liderança — VALIDADO em produção real, apoiador se autocadastrou pelo link de uma liderança específica com sucesso; anexo de documento financeiro via Cloudflare R2 também validado. Próximo: em aberto — ver seção 9)

---

## ⚠️ LEIA ISTO PRIMEIRO — como este documento funciona entre conversas

Preciso ser transparente com você sobre uma limitação técnica importante, porque ela afeta como vamos trabalhar nas próximas semanas/meses:

**Eu não tenho memória automática de arquivos entre conversas diferentes.** Cada conversa nova comigo começa "do zero" em termos de arquivos e ambiente de container — eu não acesso sozinho o que foi gerado numa conversa anterior.

Isso significa que **este arquivo é, literalmente, minha única fonte de contexto entre uma sessão e outra** — exatamente como você pediu que ele fosse. Na prática, o fluxo correto é:

1. **Você salva este arquivo no repositório GitHub do projeto** (ex: `docs/PROJETO-FONTE-DA-VERDADE.md`, na raiz do repo).
2. **No início de cada nova conversa comigo**, você faz upload deste arquivo (a versão mais atualizada do repo) antes de pedirmos para começar um módulo novo.
3. **Eu leio o arquivo, confirmo o estado do projeto com você, e só então seguimos.**
4. **Ao final de cada módulo**, eu gero a versão atualizada deste arquivo (com as novas decisões, módulo marcado como concluído, etc.) e você comita no repositório.

Esse é o mecanismo real que vai garantir a consistência que você pediu — não é uma memória "mágica" minha, é este documento fazendo esse papel deliberadamente. Isso é, inclusive, uma prática real de engenharia: é literalmente um **ADR (Architecture Decision Record)** consolidado + **project charter**, algo que times sênior mantêm em qualquer projeto de longo prazo, com ou sem IA envolvida.

---

## 1. Visão Geral

- **Nome do projeto:** CampanhaOS
- **O que é:** SaaS multi-tenant para gestão de campanhas eleitorais (vereador até governador/senador), com CRM de eleitores, lideranças, agenda, financeiro, jurídico, pesquisas, IA generativa/RAG e comunicação (WhatsApp oficial).
- **Usuário do sistema:** cada campanha é um *tenant* isolado; dentro dela, papéis (Administrador, Coordenador, Marketing, Financeiro, Jurídico, Cabo Eleitoral, Atendente, Voluntário) com permissões granulares.
- **Escala alvo:** milhares de tenants simultâneos, milhões de registros, escalável horizontalmente.
- **Documento de requisitos completo (Fase 1):** ver `fase-1-requisitos-arquitetura.md` — este documento aqui é o resumo *vivo e operacional*; o outro é o registro histórico da decisão original.

---

## 2. Decisões Arquiteturais Consolidadas (ADR)

### ADR-001 — Estilo arquitetural
**Decisão:** Clean Architecture + DDD tático + Hexagonal (Ports & Adapters), organizado como monólito modular (bounded contexts desacoplados, prontos para extração futura em serviços independentes se necessário).
**Camadas:** `domain` → `application` (casos de uso) → `infrastructure` (adapters concretos) → `presentation` (API/workers).
**Status:** Aprovado, Fase 1.

### ADR-002 — Multi-tenancy
**Decisão:** Schema único compartilhado + coluna `tenant_id` em toda tabela de negócio + **Row-Level Security (RLS)** do PostgreSQL como camada de proteção adicional (não substitui filtro na aplicação, reforça).
**Motivo:** único modelo que escala para milhares de tenants/milhões de registros sem explosão de objetos de banco.
**Status:** Aprovado, Fase 1. **Regra inegociável: nenhuma tabela de negócio nasce sem `tenant_id` + política RLS correspondente.**

### ADR-003 — Stack Backend
- Python 3.12+ / FastAPI (async) / SQLAlchemy 2.0 async / Alembic / Pydantic v2
- Celery + Redis (filas e cache)
- PostgreSQL (com PostGIS quando o módulo de mapas entrar)
- Autenticação: JWT + Refresh Token rotacionado, blocklist de revogação em Redis
**Status:** Aprovado, Fase 1.

### ADR-004 — Stack Frontend
- React + TypeScript + Vite
- TailwindCSS + Shadcn UI
- React Query (estado servidor) + React Router
**Status:** Aprovado, Fase 1.

### ADR-005 — Infraestrutura
- Docker + Docker Compose (dev) → Coolify/Railway (staging) → AWS (produção)
- NGINX (reverse proxy/TLS)
- GitHub + GitHub Actions (CI/CD) — **repositório GitHub do usuário já disponível**
- Observabilidade: Sentry (erros), Prometheus + Grafana (métricas), OpenTelemetry (tracing)
**Status:** Aprovado, Fase 1.

### ADR-006 — Testes
- Pytest, mínimo 80% de cobertura no domínio e casos de uso.
**Status:** Aprovado, Fase 1.

### ADR-007 — Conformidade legal (não-técnica, mas vinculante ao design)
- Toda automação de comunicação (WhatsApp, e-mail) deve usar apenas APIs oficiais, respeitando termos de uso das plataformas e legislação eleitoral/TSE aplicável.
- Todo dado pessoal de eleitor registra `legal_basis` (base legal LGPD) desde a criação do schema.
- Validação jurídica de conformidade eleitoral/LGPD é de responsabilidade do usuário/seu jurídico — eu sinalizo riscos técnicos conhecidos, não substituo essa validação.
**Status:** Vinculante desde a Fase 1.

### ADR-008 — Separação entre usuário de migração e usuário de aplicação no PostgreSQL
**Decisão:** dois usuários de banco distintos. `campanhaos` (definido em `POSTGRES_USER`) é o superusuário criado pela imagem oficial do Postgres — usado **só** para rodar migrações Alembic (`MIGRATION_DATABASE_URL`). `campanhaos_app` é um usuário sem privilégio de superuser, criado pela migração `0002_create_app_role`, com apenas SELECT/INSERT/UPDATE/DELETE nas tabelas — é o único usuário que a aplicação usa em runtime (`DATABASE_URL`).
**Motivo:** descoberto durante os testes de isolamento de tenant (Módulo 1 / Bloco F): superusuários do PostgreSQL **sempre ignoram Row-Level Security**, mesmo com `FORCE ROW LEVEL SECURITY` — isso não é configurável via policy, é uma regra do próprio banco. Sem essa separação, o ADR-002 (multi-tenancy via RLS) nunca teria efeito real, mesmo com todas as policies corretas.
**Status:** Aprovado, Módulo 1 / Bloco F. **Regra inegociável a partir de agora: a aplicação NUNCA se conecta ao banco com um usuário superuser.**

### ADR-009 — Super-admin sem bypass de RLS; billing sem integração de pagamento real (MVP)
**Decisão:** duas escolhas de escopo tomadas em conjunto com o usuário no Módulo 7:
1. O super-admin **não** usa uma role de banco com `BYPASSRLS`. Operações sobre um tenant específico (ex: atribuir assinatura) usam o mesmo mecanismo (`TenantContextSetter`) que usuários normais — "declarar" o tenant que está sendo operado. Isso significa que **não existe relatório agregado cross-tenant** nesta versão (ex: "todas as assinaturas de todos os tenants numa tabela só").
2. Billing entrega o **modelo de dados** (`Plan`, `Subscription`) e o painel de gestão, mas **não integra com Stripe/Mercado Pago/PIX de verdade** — não há cobrança real. Foi decisão consciente: Claude não tem como testar chamadas reais a essas APIs nem validar webhooks sem credenciais/endpoint público.
**Motivo:** pressão de prazo real do usuário (lançamento de piloto fechado com 1-2 campanhas reais) — escopo reduzido ao que dá pra construir e validar com confiança no tempo disponível, deixando bypass de RLS e gateway de pagamento como evoluções futuras bem definidas, não bloqueando o lançamento.
**Status:** Aprovado, Módulo 7.

### ADR-010 — Uso real do sistema é para eleição em andamento (LGPD + TSE)
**Contexto crítico registrado em 06/08/2026:** o usuário confirmou que o piloto vai rodar com dado real de eleitor, para campanha eleitoral **de verdade**, em eleição em andamento.
**Implicações levantadas (não resolvidas por código, apenas sinalizadas):**
- Prestação de contas oficial para as Eleições 2026 é feita pelo **Conta+JE** (TSE) — substituiu o antigo SPCE. Candidatos são obrigados a reportar receitas em até 72h do recebimento. **O módulo Financeiro do CampanhaOS não é e não pode ser tratado como substituto do Conta+JE** — é controle interno/organizacional apenas. Isso precisa ficar explícito para quem for usar o piloto.
- LGPD: campo `legal_basis` já existe no schema de `Voter` desde o Módulo 2, mas nenhuma validação jurídica formal foi feita sobre o fluxo de consentimento/tratamento de dado real de eleitor.
- Claude não é advogado e não pode validar conformidade legal — recomendação registrada ao usuário: validação jurídica antes de tratar dado real de eleitor em campanha ativa.
**Status:** Risco registrado, não mitigado por código. Requer decisão/validação do usuário fora do escopo de desenvolvimento.

---

## 3. Convenções do Projeto

> Estas convenções ainda **não foram testadas em código real** (viremos a validar/ajustar na Fase 2). Trate como ponto de partida.

- **Versionamento de API:** `/api/v1/...` desde o primeiro endpoint.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`) — facilita changelog automático depois.
- **Branches:** `main` (produção) ← `develop` (integração) ← `feature/<modulo>-<descricao>`.
- **Nomenclatura de tabelas:** snake_case, plural (`voters`, `leaderships`, `finance_transactions`).
- **Nomenclatura de código Python:** PEP8, type hints obrigatórios em funções públicas.
- **Nomenclatura de componentes React:** PascalCase, um componente por arquivo, colocation por feature (`features/voters/components/...`).
- **Idioma do código:** nomes de variáveis/funções/classes em **inglês** (padrão de mercado); textos de UI e comentários de negócio em **português** quando fizer sentido para o domínio (ex: `estimated_votes` no código, mas rótulos como "Votos Estimados" na UI).
- **Docker: rebuild vs. restart vs. recreate:** mudanças em `src/`, `alembic/` ou `tests/` (bind mounts) exigem só `docker compose restart backend`. Mudanças em `pyproject.toml`, `Dockerfile` ou `docker-compose.yml` exigem `docker compose up -d --build`. Mudanças no `.env` são as mais traiçoeiras: `docker compose up -d` nem sempre detecta mudança de CONTEÚDO de um `env_file` (só detecta com confiança se o caminho do arquivo mudar) — o jeito confiável é `docker compose up -d --force-recreate backend`. Na dúvida, `--force-recreate` (ou `down` + `up -d`) nunca está errado, só é mais lento. Verificar com `docker compose exec backend sh -c "echo $VARIAVEL"` sempre que uma mudança de `.env` for crítica.

---

## 4. Estrutura de Pastas Oficial

```
backend/src/{domain, application, infrastructure, presentation, config}/
frontend/src/{features, shared, routes}/
```
(estrutura completa e detalhada está no documento de Fase 1 — não vou duplicar aqui para evitar os dois documentos divergirem; qualquer mudança na estrutura de pastas deve ser refletida nos dois lugares).

---

## 5. Mapa de Módulos do Sistema

| # | Módulo | Status | Depende de | Observações |
|---|---|---|---|---|
| 0 | Setup do monorepo (Docker, CI, estrutura base) | ✅ Concluído e auditado | — | Ver seção 6.1 para detalhes e como validar localmente |
| 1 | Tenants + Auth (JWT, RBAC) | ✅ Concluído e validado end-to-end | Módulo 0 | Base de tudo — RLS implementado e validado com testes reais. RBAC básico (papéis/permissões no schema) existe; atribuição de papéis a usuários fica para módulo de gestão de equipe |
| 2 | CRM de Eleitores | ✅ Concluído e validado end-to-end | Módulo 1 | CRUD completo, filtro por tag, busca, paginação, soft delete |
| 3 | Lideranças | ✅ Concluído e validado end-to-end | Módulo 2 | CRUD completo + associação Eleitor↔Liderança (leadership_id) |
| 4 | Agenda | ✅ Concluído e validado end-to-end | Módulo 1 | CRUD completo + associação opcional com Eleitor e Liderança |
| 5 | Frontend base (login + dashboard + CRUD eleitores) | ✅ Concluído e validado end-to-end | Módulos 1-2 | React/Vite/TS/Tailwind/Shadcn, 11 testes automatizados (Vitest+RTL) |
| 6 | Financeiro (básico) | ✅ Concluído e validado end-to-end | Módulo 1 | CRUD + resumo/saldo (Decimal, CHECK constraint) |
| 7 | Billing (Stripe/MP/PIX) + painel super-admin | ✅ Concluído — modelo de dados + painel; integração real com gateway de pagamento adiada por decisão (ver ADR-009) | Módulo 1 | Auth dupla (usuário/super-admin), RLS seletivo, `PlatformAdmin` separado de `User` |
| 8 | IA multi-provedor + RAG | 🔲 Não iniciado | Módulos 2, 5 | Adiado — ver priorização abaixo |
| — | **Módulo de Deploy** (inserido por decisão de negócio, 06/08) | ✅ Validado em produção real — backend Railway + frontend Vercel, ambos respondendo | Módulo 0 | Ver seção 6.9 (atualizada) e `RUNBOOK-DEPLOY.md`. URLs: backend `campanhaos-production.up.railway.app`, frontend `campanha-jf8fmq31g-dedecobbs-projects.vercel.app` |
| — | **Frontend: Lideranças, Agenda, Financeiro** (inserido por decisão de negócio, 06/08) | ✅ Concluído e validado em produção real | Módulos 3, 4, 6, 5 | 19 arquivos, mesmo padrão de `features/voters/`. Testado pelo usuário em produção (CORS, telas, resumo financeiro) |
| 9+ | WhatsApp oficial, app cabo eleitoral, monitoramento, pesquisas, jurídico | 🔲 Não iniciado | Conforme priorização | Depois do piloto |

**Legenda:** 🔲 Não iniciado · 🟡 Em andamento · ✅ Concluído e auditado

**Regra de trabalho:** cada conversa nova desenvolve **um único módulo** desta lista, seguindo o rito completo: contexto → função do módulo → dependências → riscos → impacto arquitetural → código → auditoria técnica final → atualização deste documento.

---

### 6.1 Módulo 0 — Setup do Monorepo (concluído)

**Arquivos entregues:**
- `backend/pyproject.toml`, `backend/src/config/settings.py`
- `backend/src/presentation/api/main.py` + `backend/src/presentation/api/v1/routers/health.py`
- `backend/Dockerfile`, `docker-compose.yml`, `.env.example`, `.gitignore`
- `.github/workflows/ci.yml`, `backend/tests/test_health.py`
- `README.md`

**Validado por:** checagem estática (TOML bem formado, sintaxe Python de todos os arquivos) rodada no ambiente de geração, **e validação real do usuário** via `docker compose up --build` (após correção do bug 4) — aplicação sobe com sucesso (`Application startup complete`).

**Bugs corrigidos durante a auditoria deste módulo** (registrados aqui para histórico, não para repetir no futuro):
1. `pyproject.toml` sem config de empacotamento do hatchling (nome do projeto ≠ pasta `src/`) — corrigido com `packages = ["src"]`.
2. CI configurado para exigir 80% de cobertura sem nenhum teste existir ainda — corrigido criando `test_health.py`.
3. README com instruções de teste local que quebrariam fora da rede Docker — corrigido com variáveis de ambiente explícitas usando `localhost`.

---

### 6.2 Módulo 1 — Tenants + Auth (concluído e validado end-to-end)

**O que foi entregue:**
- **Domínio:** entidades `Tenant`/`User` (dataclasses puras), Value Object `Email`, interfaces `TenantRepository`/`UserRepository`
- **Infraestrutura de banco:** models SQLAlchemy (`Tenant`, `User`, `Role`, `Permission`, `UserRole`, `RolePermission`), 3 migrações Alembic (`0001_initial_schema`, `0002_create_app_role`, `0003_sync_app_role_password`), repositories reais, mecanismo de contexto de tenant para RLS
- **Aplicação:** casos de uso `RegisterTenantUseCase`, `LoginUseCase`, `RefreshTokenUseCase` (com rotação), portas de segurança (`PasswordHasher`, `TokenService`, `RefreshTokenBlocklist`, `TenantContextSetter`)
- **Segurança:** `BcryptPasswordHasher`, `JwtTokenService` (access/refresh diferenciados), `RedisRefreshTokenBlocklist`
- **API:** endpoints `/api/v1/auth/{register,login,refresh,me}`, handlers globais de exceção, injeção de dependência centralizada
- **Testes:** 10 testes automatizados (fluxo completo via API + isolamento de tenant via RLS de baixo nível), 87% de cobertura

**Validado por:** execução real completa pelo usuário — `docker compose exec backend pytest -v --cov=src` → **10 passed**, incluindo os 3 testes de RLS que prova ativamente que um tenant não consegue ler/escrever dados de outro, mesmo via SQL cru sem filtro.

**Decisão de segurança mais importante do módulo (ADR-008):** a aplicação nunca se conecta ao PostgreSQL como superusuário — existe um usuário `campanhaos_app` dedicado, sem esse privilégio, criado pela migração `0002`. Migrações continuam rodando com o usuário superuser (`MIGRATION_DATABASE_URL`).

**Limitações conhecidas, registradas conscientemente (não são bugs, são escopo adiado):**
- Atribuição de papéis (`Role`) a usuários ainda não tem caso de uso/endpoint — usuário criado no registro não tem papel atribuído ainda.
- `user_roles`/`role_permissions` não têm RLS direto, só proteção indireta via JOIN com tabelas que têm RLS.
- MFA, recuperação de senha e controle de sessão avançado (RF-01) ficam para uma iteração futura do módulo de Auth.

**Processo:** este módulo teve ~18 bugs encontrados e corrigidos em conjunto com o usuário rodando cada etapa em ambiente real — a maioria de infraestrutura (Docker, variáveis de ambiente, pool de conexões, privilégios de banco), não de lógica de negócio. O histórico completo está no changelog (seção 8) para consulta futura caso um problema parecido reapareça em outro módulo.

---

### 6.3 Módulo 2 — CRM de Eleitores (concluído e validado end-to-end)

**O que foi entregue:**
- **Domínio:** entidade `Voter` (com validação de base legal LGPD, tags normalizadas, soft delete), interface `VoterRepository` com filtros/paginação desde o desenho
- **Infraestrutura de banco:** `VoterModel` (array de tags com índice GIN, JSONB para campos personalizáveis), migração `0004_create_voters` (RLS no mesmo padrão do Módulo 1), `SqlAlchemyVoterRepository`
- **Aplicação:** 5 casos de uso (criar, buscar, listar com filtro/paginação, atualizar parcial, excluir/soft-delete), hierarquia de exceções consolidada em `application/shared/`
- **API:** `/api/v1/voters` completo (POST, GET lista, GET por id, PATCH, DELETE), todos autenticados
- **Testes:** 11 testes novos (8 de fluxo via API + 3 de isolamento de tenant via RLS de baixo nível) — total do projeto: 20 testes, 87% de cobertura

**Validado por:** execução real completa pelo usuário — 20 passed.

**Achado importante deste módulo (Bug 19):** todas as colunas de timestamp do projeto usavam `TIMESTAMP WITHOUT TIME ZONE`, incompatível com os datetimes timezone-aware que o domínio sempre gera (`datetime.now(UTC)`). Só quebrou agora porque foi o primeiro caso (`soft_delete`) de um timestamp gerado em Python sendo enviado ao banco. Corrigido na causa raiz para TODAS as tabelas (migração `0005_use_timestamptz`), não só em `voters` — evita o mesmo bug reaparecer em módulos futuros.

**Decisões de escopo registradas conscientemente:**
- Busca por nome/telefone usa `ILIKE` com índice B-tree simples — não é o ideal para "contém em qualquer posição" em escala de milhões de linhas. Melhoria futura conhecida: extensão `pg_trgm` do PostgreSQL.
- Qualquer usuário autenticado do tenant pode criar/editar/excluir eleitores — não há checagem de permissão granular ainda (RBAC sem atribuição de papéis, limitação já registrada desde o Módulo 1).
- Campos "totalmente" personalizáveis (schema dinâmico completo) não foram implementados — `tags` + `custom_fields` (JSONB) cobrem o MVP, como já decidido na Fase 1.

---

### 6.4 Módulo 3 — Lideranças (concluído e validado end-to-end)

**O que foi entregue:**
- **Domínio:** entidade `Leadership` (validação de nível de influência, estimativa de votos e tamanho de equipe não-negativos), interface `LeadershipRepository`; `Voter` atualizado com `leadership_id` opcional e o padrão de sentinela (`_UNSET`) para distinguir "não mexer" de "remover associação"
- **Infraestrutura:** `LeadershipModel`, coluna `leadership_id` em `voters` (FK `ON DELETE SET NULL`), migrações `0006_create_leaderships` e `0007_add_leadership_id_to_voters` (RLS no mesmo padrão), `SqlAlchemyLeadershipRepository`
- **Aplicação:** 5 casos de uso de lideranças + atualização de `CreateVoterUseCase`/`UpdateVoterUseCase` para validar a associação cross-entity (liderança precisa existir e pertencer ao mesmo tenant)
- **API:** `/api/v1/leaderships` completo + `leadership_id` em `/api/v1/voters`, com `request.model_fields_set` resolvendo o sentinela na fronteira HTTP
- **Testes:** 14 testes novos (10 de fluxo/associação via API + 3 de RLS de baixo nível + already contado) — total do projeto: **34 testes, 87% de cobertura**

**Validado por:** execução real completa pelo usuário — 34 passed, **sem nenhum bug novo encontrado no processo** (primeira vez isso acontece desde o Módulo 0) — sinal de que o padrão arquitetural e a infraestrutura de teste amadureceram o suficiente.

**Padrão consolidado neste módulo — o sentinela de 3 camadas:** domínio (`Voter._UNSET`) → aplicação (`voters/dto.py: UNSET`, exportado) → API (`request.model_fields_set`). Vale reaproveitar esse padrão sempre que um campo opcional-e-anulável (nullable FK, por exemplo) precisar da mesma semântica de PATCH em módulos futuros (ex: Agenda referenciando responsável, Financeiro referenciando categoria).

---

### 6.5 Módulo 4 — Agenda (concluído e validado end-to-end)

**O que foi entregue:**
- **Domínio:** entidade `Event` (tipo, status, validação de período `starts_at`/`ends_at` recalculada corretamente em updates parciais), interface `EventRepository`; associação opcional com `Voter` e `Leadership` via dois sentinelas independentes
- **Infraestrutura:** `EventModel` (duas FKs para `users`: criador e responsável), migração `0008_create_events` (RLS, depende de `0007`), `SqlAlchemyEventRepository` (ordenação cronológica)
- **Aplicação:** 5 casos de uso, com `CreateEventUseCase`/`UpdateEventUseCase` validando até 3 entidades relacionadas (responsável, eleitor, liderança)
- **API:** `/api/v1/events` completo, responsável opcional (default: usuário autenticado)
- **Testes:** 15 testes novos (12 de fluxo/validação/associação via API + 3 de RLS de baixo nível) — total do projeto: **49 testes, 86% de cobertura**

**Validado por:** execução real completa pelo usuário — 49 passed, **segundo módulo seguido sem nenhum bug novo** encontrado no processo (Módulo 3 e Módulo 4).

**Decisão de escopo registrada:** integração com Google Calendar e lembretes automáticos (parte do RF-06 original) ficam marcados 🔵 (fora do MVP), como já estava decidido desde a Fase 1.

---

### 6.6 Módulo 5 — Frontend Base (concluído e validado end-to-end)

**O que foi entregue:**
- **Setup:** React 18 + Vite + TypeScript (strict) + TailwindCSS v3 + Shadcn UI (componentes copiados: Button, Input, Label, Card, Table, Select) + React Router + React Query + Vitest/React Testing Library
- **Autenticação:** `AuthContext` (access token em memória, refresh token em `sessionStorage`), interceptor axios com renovação automática em 401 (single-flight, testado isoladamente), `ProtectedRoute`, página de login
- **CRUD de Eleitores:** listagem paginada com busca, criação, edição, exclusão (`VotersListPage`, `VoterFormPage`, `VoterForm` reaproveitado nos dois modos)
- **Testes:** 11 testes automatizados (ProtectedRoute, LoginPage, VoterForm) cobrindo os fluxos e validações mais importantes

**Validado por:** `tsc` local (sem instalar pacotes) pegou 2 bugs de configuração antes mesmo do usuário rodar `npm install`; depois, execução real do usuário — `npm test` → 11 passed, e teste manual completo no navegador (login real + CRUD de eleitores conversando com o backend de verdade).

**Decisões de segurança registradas:**
- Access token em memória (nunca persiste) + refresh token em `sessionStorage` — trade-off documentado no código; a solução ideal (cookie `httpOnly`) exigiria mudança no backend, fora de escopo deste módulo.

**Limitações conhecidas, registradas conscientemente:**
- Login exige `tenant_id` (UUID) digitado manualmente — não existe endpoint de busca de campanha por nome ainda.
- Formulário de eleitor não expõe `latitude`/`longitude`/`custom_fields`/`leadership_id` (exigiriam seletor de mapa e combobox de lideranças).
- Exclusão usa `window.confirm` nativo, não um modal customizado.
- Dashboard é só uma saudação — métricas/gráficos reais (RF-03) ficam para módulo futuro.

---

### 6.7 Módulo 6 — Financeiro Básico (concluído e validado end-to-end)

**O que foi entregue:**
- **Domínio:** entidade `FinanceTransaction` usando `Decimal` (nunca `float`) para valores monetários, `amount` sempre positivo com o `type` determinando o sinal (`signed_amount`), `FinanceSummary` com cálculo de saldo
- **Infraestrutura:** `FinanceTransactionModel` (`NUMERIC(12,2)`), migração `0009_create_finance_transactions` com RLS **e** `CHECK CONSTRAINT amount > 0` (segunda camada de defesa, testada isoladamente), `SqlAlchemyFinanceRepository` com resumo calculado via `SUM`/`GROUP BY` no banco
- **Aplicação:** 5 casos de uso; `ListFinanceTransactionsUseCase` retorna resumo respeitando os mesmos filtros da listagem
- **API:** `/api/v1/finance` completo, com `Decimal` funcionando nativamente no Pydantic/Swagger
- **Testes:** 13 testes novos (9 de fluxo/resumo via API + 4 de baixo nível: 3 de RLS + 1 de CHECK constraint) — total do projeto: **62 testes, 86% de cobertura**

**Validado por:** execução real completa pelo usuário — 62 passed, **nenhum bug novo encontrado nesta rodada** (backend com padrão bastante maduro a esta altura).

**Decisão de escopo registrada (já vinha da Fase 1):** prestação de contas no formato oficial do TSE continua fora do MVP (🔵) — é um formato regulatório específico que mereceria pesquisa própria.

---

### 6.8 Módulo 7 — Billing + Painel Super-Admin (concluído e validado end-to-end)

**O que foi entregue:**
- **Domínio:** `Plan` (catálogo global, sentinela para limites ilimitados), `Subscription` (1:1 com tenant, RLS), `PlatformAdmin` (separado de `User`, sem RLS)
- **Infraestrutura:** 3 tabelas novas (migrações `0010`-`0012`), `TenantRepository` estendido com `list_paginated` (Módulo 1 ganhou capacidade nova)
- **Aplicação:** autenticação de super-admin completamente separada (JWT com namespace de tipo distinto), gestão de tenants reaproveitando `Tenant.suspend()`/`activate()` do Módulo 1, CRUD de planos, atribuição de assinatura sem bypass de RLS (ADR-009)
- **API:** `/api/v1/admin/auth/*`, `/api/v1/admin/tenants/*`, `/api/v1/admin/plans/*`, `/api/v1/admin/tenants/{id}/subscription`
- **Script de bootstrap:** `scripts/create_platform_admin.py` (sem endpoint público de registro, por segurança)
- **Testes:** 23 testes novos, incluindo `test_admin_security_boundary.py` — prova formal de que token de usuário normal e token de super-admin nunca funcionam um no lugar do outro — total do projeto: **84 testes, 86% de cobertura**

**Validado por:** execução real completa pelo usuário — 84 passed. Processo de validação teve confusão real de nomes de arquivo repetidos entre pastas (`admin_auth.py` existindo em `routers/` e `schemas/` simultaneamente) — 2 rodadas de correção até resolver, sem bug de lógica, só de organização de arquivo.

**Decisões de escopo registradas (ADR-009, ADR-010):** sem bypass de RLS pro super-admin (sem relatório agregado cross-tenant); sem integração real de gateway de pagamento; risco de compliance TSE/LGPD sinalizado ao usuário para uso real em campanha eleitoral (Conta+JE é o sistema oficial, não este).

---

### ADR-011 — Hospedagem: Railway (backend+Postgres+Redis) + Vercel (frontend)
**Decisão:** dois provedores, cada um na sua força. Backend/Postgres/Redis no Railway (deploy via Dockerfile já existente, Postgres/Redis gerenciados). Frontend no Vercel (detecção automática de projeto Vite, deploy por git push, HTTPS automático).
**Alternativa descartada:** Supabase para "rodar o backend" — tecnicamente inviável. Supabase é Postgres + Auth própria + Storage + Edge Functions (Deno), não um host genérico de aplicação Python/FastAPI. Usar Supabase só como banco (ignorando a API/Auth deles) exigiria um terceiro serviço separado só para rodar o FastAPI, aumentando complexidade sem reduzir custo/esforço.
**Limitação técnica encontrada:** Railway não suporta selecionar um `target` específico de Dockerfile multi-stage — resolvido com `Dockerfile.production` dedicado (só os stages de build/runtime, sem o stage `dev`).
**Status:** Aprovado, Módulo de Deploy. Configuração pronta em `backend/railway.json`, `backend/Dockerfile.production`, `frontend/vercel.json`; passo a passo completo em `RUNBOOK-DEPLOY.md`.

### 6.9 Módulo de Deploy (configuração pronta — validação real pendente)

**O que foi entregue:**
- Correção de bug real: CORS ficava fechado para qualquer origem em produção (nunca configurado corretamente desde o Módulo 0) — corrigido com `settings.frontend_url`
- Sentry inicializado de verdade (estava instalado desde o Módulo 0, nunca chamado)
- `Dockerfile.production` + `railway.json` (backend): migração encadeada no start, healthcheck, restart policy
- `vercel.json` (frontend): rewrite para SPA (React Router)
- Backup: script `pg_dump` + GitHub Actions agendado (diário, artefato de 30 dias) — decisão consciente de não depender só do backup nativo do provedor
- `RUNBOOK-DEPLOY.md`: passo a passo completo, do zero até o piloto no ar, com checkpoints de validação em cada etapa

**Transparência sobre o que NÃO pude validar:** não tenho acesso a Railway/Vercel/GitHub Actions reais — todo este módulo foi escrito e revisado estaticamente, sem execução real (diferente de todos os módulos de código anteriores, onde eu conseguia rodar testes). A validação real é 100% do usuário, seguindo o runbook.

**ATUALIZAÇÃO 06/08 — validação real concluída, com aprendizados importantes:**

O deploy real revelou vários bugs que a validação estática não conseguiria pegar. Lição central, válida pra qualquer módulo futuro que envolva Railway: **o `railway.json` do repositório sempre sobrescreve qualquer configuração feita na tela do painel** — editar pela interface visual não tem efeito nenhum enquanto o campo equivalente existir no arquivo. Isso causou a maior parte do tempo de debug (comando de início, healthcheck, tudo precisou ser configurado via arquivo, não pela tela).

**Bugs reais encontrados e corrigidos durante o deploy:**
1. Variáveis de ambiente do Railway inicialmente copiadas do `.env` local (senhas/hosts que só existem no Docker local) — corrigido com valores reais de produção
2. Porta do backend não fixada — Railway não detecta target de Dockerfile multi-stage nem porta automaticamente sem `EXPOSE` explícito
3. `railway.json` sobrescrevendo configuração da tela (comando de início E healthcheck) — causa raiz da maior parte do tempo gasto
4. `tsconfig.node.json`: `allowImportingTsExtensions` conflitando com `composite: true` (só aparece no `tsc -b` real, não no `tsc --noEmit` usado na validação local do Módulo 5)
5. `tsconfig.json`: `ignoreDeprecations: "6.0"` inválido na versão de TypeScript real do ambiente de build (diferente da usada na validação local) — corrigido removendo `baseUrl` inteiramente
6. `vite.config.ts`/`vitest`: conflito de tipos entre a cópia do Vite usada pelo `vitest` e a cópia direta do projeto — corrigido separando `vitest.config.ts` de `vite.config.ts` (padrão oficial do Vitest via `mergeConfig`)

**Padrão que se repetiu bastante:** minha validação local (rodando `tsc`/testes num ambiente que eu controlo) não pegou vários desses bugs, porque o ambiente de build real (Vercel) usa versões/configurações ligeiramente diferentes. Isso não invalida a prática de validar antes de entregar — só confirma que validação estática nunca substitui 100% a execução real no ambiente de destino.

---

### ADR-012 — Geocodificação: Mapbox v6 estruturado + ajuste manual como rede de segurança
**Decisão:** geocodificação automática de endereço de eleitor via Mapbox Geocoding API v6, com **entrada estruturada** (`address_line1`, `place`, `region`, `postcode`, `neighborhood` como parâmetros separados — não uma string única concatenada). Além disso, um **ajuste manual de pino** (arrastar num mapa) sempre disponível na edição do eleitor, como rede de segurança final.
**Motivo:** a primeira tentativa (v5, string única concatenada) colocou eleitores no **estado errado** — a v6 estruturada corrigiu a maior parte dos casos, mas ruas internas de condomínio fechado (nome genérico tipo "Rua Três", sem mapeamento público) continuam sem solução automática possível — isso é limite real de cobertura de dado do provedor, não bug de código. Para esses casos, o ajuste manual é a única solução que funciona sempre, independente da qualidade do dado do Mapbox pra aquele lugar específico.
**Trade-off técnico registrado:** quando o usuário ajusta o pino manualmente, essa coordenada fica "travada" (não é mais sobrescrita por geocodificação automática em edições futuras) — controlado por uma flag `locationManuallyAdjusted` que só existe no estado do formulário do frontend (não persistida no backend). O backend distingue "coordenada manual" de "deixar geocodificar" pela simples presença/ausência de `latitude`/`longitude` no payload da requisição.
**Status:** Aprovado e implementado.

### 6.10 Mapa de Eleitores (concluído)

**O que foi entregue:**
- **Domínio:** `Voter` ganhou `city`, `state`, `postal_code`, `neighborhood` (Módulo 2 original só tinha `address` livre)
- **Geocodificação:** `GeocodingService` (porta) + `MapboxGeocodingService` (Mapbox Geocoding API v6, entrada estruturada) — conectado em `CreateVoterUseCase`/`UpdateVoterUseCase`, nunca bloqueia a operação se falhar
- **Endpoint dedicado:** `GET /voters/map` — leve, com teto de 1000 registros (não paginado, mas também não "sem limite", respeitando o princípio já documentado do projeto)
- **Frontend:** tela de mapa (`/mapa`, Mapbox GL JS), formulário de eleitor com campos de endereço estruturado, e `LocationPicker` (pino arrastável) para ajuste manual quando a geocodificação automática não acerta
- **Migrações:** `0013_add_voter_address_detail`, `0014_add_voter_neighborhood`

**Bugs reais encontrados e corrigidos durante o deploy (fora do ambiente local, só apareceram em produção real):**
1. `httpx` estava em dependências de teste (`dev`), não em produção — nunca tinha sido usado em código de produção real até a geocodificação
2. `mapbox_access_token` faltando no `settings.py` que foi de fato enviado pro Railway (arquivo desatualizado)
3. Nome de revisão do Alembic (`0013_add_address_detail_to_voters`, 33 caracteres) estourou o limite de 32 caracteres da coluna `alembic_version.version_num` — encurtado para `0013_add_voter_address_detail`
4. Geocodificação v5 (string única) colocou eleitor em estado errado — corrigido migrando para v6 com entrada estruturada

**Limitação registrada conscientemente:** geocodificação automática não tem como acertar 100% dos casos — ruas internas de condomínios fechados, loteamentos não mapeados publicamente, etc. O ajuste manual de pino é a solução definitiva para esses casos, não um "quebra-galho".

---

### ADR-013 — WhatsApp: opt-in obrigatório via BSP (Twilio), nunca disparo em massa
**Decisão:** integração de WhatsApp através de um BSP (Business Solution Provider) autorizado pela Meta — Twilio na implementação concreta —, com opt-in registrado (`WhatsAppContact`) só quando o CONTATO inicia a conversa. Envio de mensagem exige template pré-aprovado e contato com opt-in ativo — verificação feita no caso de uso (`SendWhatsAppTemplateMessageUseCase`), não confiável só pela camada de API.
**Motivo:** decisão de compliance tomada em conjunto com o usuário — a Resolução TSE 23.610/2019 (atualizada pra 2026) proíbe explicitamente disparo em massa de mensagens político-eleitorais, e determina que listas de transmissão só valem se o contato "adicionou o número do candidato" por conta própria. Uso indevido já causou cassação de candidatura em pleitos anteriores (2018, 2020, 2022, 2024). BSP em vez de conta Meta direta: reduz fricção de onboarding, continua 100% dentro da API oficial.
**Trade-off técnico registrado:** webhook do Twilio é endpoint público (sem JWT) — segurança vem da verificação de assinatura HMAC-SHA1 (validada contra o vetor de teste oficial do Twilio), não de autenticação de usuário. Como não há `CurrentUser` nesse endpoint, o contexto de tenant (RLS) precisa ser declarado manualmente — único lugar do projeto onde isso acontece fora do fluxo padrão de `get_current_user`.
**Limitação de escopo (MVP):** roteamento de tenant no webhook via `tenant_id` na query string da URL configurada manualmente no painel do Twilio — não é autoatendimento, cada campanha nova exige configuração manual. Aceitável para o volume do piloto (1-2 campanhas).
**Status:** Backend aprovado, implementado e testado (93 testes). **Validado end-to-end em produção real em 16/08/2026** — mensagem real do WhatsApp → Twilio → webhook → opt-in registrado, confirmado via API.

**ATUALIZAÇÃO 16/08 — dois bugs reais encontrados na validação real, ambos corrigidos:**
1. `python-multipart` faltando nas dependências — `request.form()` do FastAPI/Starlette exige esse pacote separado, nunca precisamos dele antes porque este é o primeiro endpoint do projeto a receber form-urlencoded em vez de JSON (webhook do Twilio manda assim, não JSON)
2. **A causa raiz do 403 "assinatura inválida"**: o `uvicorn`, mesmo com `--proxy-headers`, só confia no header `X-Forwarded-Proto` (que diz se a requisição original era HTTPS) se a conexão vier de `127.0.0.1` — como o proxy do Railway não é localhost, o header era ignorado, e a URL reconstruída internamente ficava `http://` em vez de `https://`, fazendo a assinatura do Twilio (calculada sobre a URL `https://`) nunca bater com a nossa. Corrigido adicionando `--forwarded-allow-ips='*'` ao comando de start. **Esse ajuste provavelmente será necessário em qualquer webhook de terceiro futuro atrás do proxy do Railway** — vale lembrar disso de cara da próxima vez, não descobrir de novo do zero.

### 6.11 WhatsApp Opt-in (backend concluído)

**O que foi entregue:**
- **Domínio:** `WhatsAppContact` (opt-in/opt-out, sempre `opt_in_source="contato_iniciou_conversa"` — sem nenhum caminho de código pra importar lista)
- **Infraestrutura:** `TwilioWhatsAppSender` (envio via Content API do Twilio), `validate_twilio_signature` (verificação HMAC-SHA1, testada contra o vetor oficial do Twilio)
- **Aplicação:** `HandleIncomingWhatsAppMessageUseCase` (opt-in/opt-out automático, detecta palavras-chave de descadastro), `SendWhatsAppTemplateMessageUseCase` (trava de compliance: nunca envia sem opt-in ativo, é impossível burlar isso via parâmetro)
- **API:** `POST /whatsapp/webhook` (público, assinatura verificada), `GET /whatsapp/contacts` e `POST /whatsapp/send` (autenticados, tenant-scoped)
- **Migração:** `0015_create_whatsapp_contacts` (RLS ativo)
- **Testes:** 14 novos (93 no total do projeto) — incluindo o teste mais crítico do módulo: enviar mensagem pra contato que perdeu o opt-in é bloqueado com 403, provado via API real, não só no caso de uso isolado

**Bug real encontrado na validação do usuário:** `WhatsAppContactNotFoundError`/`ContactNotOptedInError` faltando no `_APPLICATION_ERROR_STATUS_MAP` do `error_handlers.py` — arquivo desatualizado (mesmo padrão de erro já visto antes na sessão: esquecer de propagar uma mudança em arquivo compartilhado entre módulos).

**Bugs reais encontrados na validação do usuário (3, todos corrigidos):**
1. `WhatsAppContactNotFoundError`/`ContactNotOptedInError` faltando no `_APPLICATION_ERROR_STATUS_MAP` do `error_handlers.py` — arquivo desatualizado
2. `python-multipart` faltando nas dependências — necessário para `request.form()` (primeiro endpoint do projeto recebendo form-urlencoded, não JSON)
3. `uvicorn --proxy-headers` sozinho não basta atrás do proxy do Railway — precisou de `--forwarded-allow-ips='*'` também, senão a URL reconstruída fica `http://` em vez de `https://`, quebrando a verificação de assinatura do Twilio

**Validado end-to-end em produção real, 16/08/2026**: mensagem WhatsApp real → Twilio → webhook → opt-in registrado, confirmado via API. Sandbox do Twilio usado para o teste (não o número de produção da campanha ainda — isso fica pra quando o piloto for lançado de verdade).

---

### ADR-014 — Gênero inclusivo, autocadastro público com link único, e limitação de taxa via Redis
**Decisão:** (1) campo de gênero com 5 opções (feminino, masculino, não-binário, prefere não informar, outro), sempre opcional; (2) autocadastro público via **um link único por campanha** (não individual por pessoa) — token gerável/revogável armazenado em `Tenant.public_registration_token`; (3) `Voter.created_by_user_id` tornou-se opcional (`None` = autocadastro, sem vínculo com usuário da equipe); (4) proteção contra spam via rate limiter próprio (Redis, janela fixa, 3 cadastros/hora por IP+tenant) — sem adicionar biblioteca nova, reaproveitando o Redis já usado pra refresh token blocklist.
**Motivo:** usuário queria mandar o link "pra quem vai apoiar" sem precisar cadastrar cada pessoa manualmente — link único, compartilhado por fora do sistema (WhatsApp pessoal, redes sociais), resolve isso sem a fricção de gerar/enviar um link por pessoa (que também esbarraria na regra de opt-in do módulo WhatsApp, já que a pessoa ainda não tem opt-in nenhum nesse momento).
**Status:** Aprovado, implementado, e **validado em produção com autocadastro real de um apoiador**.

### 6.12 Gênero/Nascimento + Autocadastro Público + Painel do Dashboard (concluído)

**O que foi entregue:**
- **Eleitor:** campos `gender` (5 opções, sempre opcional) e `birth_date` (opcional)
- **Autocadastro público:** `Tenant.public_registration_token` (gerável/revogável pela campanha, tela dedicada `/link-cadastro`), endpoint público `POST /public/registration/{token}` (sem login, exige `consent_given=true`, rate limit de 3/hora por IP)
- **Painel do início:** `GET /dashboard/stats` — total de eleitores, autocadastro vs. equipe, gênero (pizza), faixa etária (barras, 6 faixas fixas: 16-17 a 60+), crescimento últimos 30 dias (linha), meta de eleitores editável com barra de progresso (`Tenant.voter_goal`)
- **Migrações:** `0016` (gender/birth_date), `0017` (registration token), `0018` (created_by_user_id opcional), `0019` (voter_goal)

**Sessão de debug excepcionalmente longa após o deploy — catálogo de causas reais, para referência futura:**
1. **Arquivos "esquecidos" na cópia pra fora desta conversa** (o mais recorrente, de longe): `VoterFormPage.tsx`, `VoterForm.test.tsx`, `types.ts` de eleitores, `dashboard_dependencies.py`, `generate_registration_token.py`, `schemas/voters.py` — todos precisaram ser reenviados individualmente depois do erro aparecer em produção. **Lição para sessões futuras**: depois de blocos grandes com muitos arquivos, vale rodar uma checagem em lote (`grep -c` por arquivo esperado) ANTES do primeiro deploy, não depois do erro.
2. **Arquivo salvo no caminho errado**: `schemas/voters.py` foi parar em `domain/voters/voters.py` por engano do usuário ao copiar/colar — só descoberto lendo a saída do `git commit` (`create mode ...`), não do erro em si.
3. **`ChatGPT/Claude não reproduziu client_ip corretamente sem X-Forwarded-For`**: mesma lição do webhook do WhatsApp, replicada de propósito no endpoint de autocadastro público desde o início (não precisou redescobrir).

**Validado em produção, 17/08/2026**: usuário mandou o link de autocadastro pra um apoiador real, que se cadastrou com sucesso; dashboard, formulário de eleitor e listagem de eleitores confirmados funcionando depois das correções.

---

### ADR-015 — Anexo financeiro via Cloudflare R2, e bug crítico de RLS descoberto (commit descarta contexto de tenant)
**Decisão:** anexo de comprovante (JPEG/PNG/PDF, até 10MB, um por lançamento) armazenado no Cloudflare R2 (compatível com S3, sem taxa de saída), upload passando pelo backend (não direto do navegador), validação de tipo por **assinatura real dos bytes** (não confia em extensão nem `Content-Type` declarado — testado explicitamente contra um `.exe` disfarçado de `.pdf`).
**Bug real descoberto e corrigido, de impacto amplo:** o contexto de tenant do RLS (`set_config(..., is_local=true)`) tem escopo de TRANSAÇÃO — é descartado automaticamente no `commit()`. Qualquer endpoint que fizesse "salva → comita → busca de novo pra montar a resposta" quebrava silenciosamente (a segunda busca rodava sem contexto de tenant, RLS bloqueava tudo, resultado interpretado como "não encontrado"). Encontrado no upload de anexo financeiro, e o MESMO bug também existia (proativamente corrigido) no endpoint de definir meta de eleitores. **Regra geral daqui pra frente: sempre ler antes de comitar, nunca depois, quando o mesmo endpoint precisa fazer as duas coisas.**
**Status:** Aprovado, implementado, bug corrigido e validado em produção.

### ADR-016 — Link de cadastro por liderança (reaproveitando o link único, sem infraestrutura nova)
**Decisão:** cada liderança tem um "link próprio" que na verdade é o MESMO link único da campanha, só com um parâmetro a mais identificando a liderança (`?lideranca={id}`) — sem token novo, sem tabela nova. Quando alguém se cadastra por esse link, o eleitor já nasce vinculado automaticamente àquela liderança. Ao cadastrar uma liderança nova, o sistema já leva direto pra tela onde o link aparece pronto pra copiar.
**Motivo:** usuário queria saber quem está trazendo mais apoiadores, sem complexidade de gerenciar tokens individuais por liderança — reaproveitar a mesma infraestrutura já existente resolveu isso de forma bem mais simples do que o desenho técnico inicial (token separado por liderança, que esbarraria em RLS e exigiria uma tabela extra).
**Validação de segurança:** um `leadership_id` inválido ou de outro tenant na URL NÃO bloqueia o cadastro — só é ignorado silenciosamente (testado explicitamente). Rastrear "quem indicou" é um bônus, nunca deveria impedir um apoiador de verdade de se cadastrar.
**Status:** Aprovado, implementado, e **validado em produção real** — apoiador se cadastrou por um link de liderança específica com sucesso.

### 6.13 Anexo Financeiro + Link de Liderança (concluído)

**O que foi entregue:**
- **Financeiro:** `attachment_storage_key/filename/content_type/size_bytes` em `FinanceTransaction`; `FileStoragePort` + `CloudflareR2Storage`; detecção de tipo por assinatura de bytes (`file_signature.py`); endpoints `POST/DELETE /finance/{id}/attachment`, `GET /finance/{id}/attachment/download-url` (link assinado, expira em 15min)
- **Liderança:** endpoint público de autocadastro aceita `leadership_id` opcional, validado contra o tenant resolvido; tela de liderança mostra o link pronto (aparece automaticamente logo após cadastrar uma liderança nova); painel do início ganhou "Eleitores por Liderança" (ranking, incluindo "Sem liderança" pra quem não tem vínculo)
- **Migração:** `0020_add_finance_attachment` (única migração nova; o link de liderança não precisou de migração nenhuma)

**Bugs reais e causas externas encontradas:**
1. Credenciais do R2 trocadas de lugar (Access Key ID ↔ Secret Access Key) — erro `Credential access key has length 64, should be 32`, bem diagnosticável pela mensagem
2. **Bug de RLS descrito no ADR-015** — o mais sério de toda a sessão, silencioso e só percebido com log de diagnóstico
3. Gráficos do painel não tinham proteção contra campo `undefined` — quebrava a página INTEIRA quando havia descompasso temporário entre o deploy do frontend (Vercel) e do backend (Railway terminando depois). Corrigido com fallback defensivo (`?? []`, `?? {}`) em todos os 4 gráficos — lição: todo componente que consome API deveria ter essa proteção por padrão, não só quando o bug aparece
4. **Incidente externo real**: GitHub teve queda generalizada (Webhooks/Actions/API) na tarde de 18/08/2026, causando fila de deploy travada na Railway por mais de 12 minutos — nada a ver com o código, resolvido sozinho quando o GitHub normalizou

**Validado em produção, 18/08/2026**: eleitor se autocadastrou por um link de liderança específica com sucesso, aparecendo corretamente na lista de eleitores e no ranking do painel.

---

## 6. Modelagem de Dados (estado atual)

**Implementadas e migradas:**
- **Módulo 1:** `tenants`, `users`, `roles`, `permissions`, `user_roles`, `role_permissions` — RLS ativo em `users`/`roles`
- **Módulo 2:** `voters` — RLS ativo, índice GIN em `tags`, `custom_fields` em JSONB; `city`/`state`/`postal_code`/`neighborhood` adicionados posteriormente (migrações `0013`, `0014`) para precisão de geocodificação
- **Módulo 3:** `leaderships` — RLS ativo; `voters.leadership_id` (FK opcional, `ON DELETE SET NULL`)
- **Módulo 4:** `events` — RLS ativo; FKs opcionais para `voters` e `leaderships`, duas FKs para `users` (criador/responsável)
- **Módulo 6:** `finance_transactions` — RLS ativo; `amount NUMERIC(12,2)` com `CHECK CONSTRAINT > 0`
- **Módulo 7:** `plans` (sem RLS, catálogo global), `subscriptions` (RLS ativo, `UNIQUE(tenant_id)`), `platform_admins` (sem RLS, `UNIQUE(email)` global)

- **Módulo Geocodificação/Mapa:** `voters` ganhou `city`/`state`/`postal_code`/`neighborhood` (migrações `0013`, `0014`)
- **Módulo WhatsApp:** `whatsapp_contacts` — RLS ativo, `UNIQUE(tenant_id, phone_number)` (migração `0015`)

- **Módulo Gênero/Autocadastro/Dashboard:** `voters` ganhou `gender`/`birth_date`, `created_by_user_id` virou opcional (migração `0018`); `tenants` ganhou `public_registration_token` (`0017`) e `voter_goal` (`0019`)

- **Módulo Anexo Financeiro:** `finance_transactions` ganhou `attachment_storage_key/filename/content_type/size_bytes` (`0020`)

Schema real em `backend/src/infrastructure/database/models.py`. Migrações `0001` a `0020`.

**Ainda conceituais, não implementadas:** `AuditLog` (transversal, ainda sem módulo dedicado).

Diagrama ER conceitual completo (incluindo as entidades ainda não implementadas) está no documento de Fase 1 (`fase-1-requisitos-arquitetura.md`). Este documento aqui reflete o que **já existe de verdade** no banco.

---

## 7. Glossário de Domínio

| Termo | Significado |
|---|---|
| Tenant | Uma campanha eleitoral cadastrada no SaaS; unidade de isolamento de dados |
| Cabo Eleitoral | Voluntário/colaborador de campo que registra visitas, apoiadores, problemas |
| Liderança | Pessoa com influência numa região que agrega/indica eleitores |
| RLS | Row-Level Security — mecanismo do PostgreSQL que restringe linhas visíveis por política |
| Base legal (LGPD) | Fundamento jurídico que autoriza o tratamento de um dado pessoal |

---

## 8. Log de Decisões (Changelog deste documento)

| Data | Mudança |
|---|---|
| 31/07/2026 | Documento criado. Consolida decisões da Fase 1 (requisitos, arquitetura, stack, multi-tenancy, cronograma). Projeto pronto para iniciar Módulo 0 (setup do monorepo). |
| 31/07/2026 | Módulo 0 concluído: monorepo, Docker Compose, FastAPI base, CI, README. 3 bugs encontrados e corrigidos em auditoria (ver seção 6.1). Pendente validação real do usuário (`docker compose up --build`) antes de iniciar Módulo 1. |
| 31/07/2026 | Bug 4 encontrado pelo usuário ao rodar `docker compose up --build`: `pyproject.toml` referenciava `readme = "README.md"`, mas o Dockerfile não copia o README (que fica na raiz do monorepo, fora de `backend/`) — build falhava na etapa de metadata do hatchling. Corrigido removendo o campo `readme` do `pyproject.toml`. Lição para o projeto: minha checagem estática (sintaxe + TOML válido) não substitui um build real; builds reais só são confiavelmente validados rodando `docker compose up --build` de verdade. |
| 31/07/2026 | Bug 5 encontrado pelo usuário ao rodar `docker compose exec backend alembic upgrade head` (Módulo 1, Bloco B): `Dockerfile` nunca copiava `alembic.ini` nem a pasta `alembic/` para dentro da imagem — Alembic não encontrava sua própria configuração. Corrigido copiando ambos no `Dockerfile` e adicionando bind mount de `./backend/alembic` no `docker-compose.yml` (para migrações futuras não exigirem rebuild de imagem). |
| 31/07/2026 | Migração `0001_initial_schema` validada com sucesso pelo usuário (`alembic upgrade head` rodou sem erros). Schema base do Módulo 1 (tenants, users, roles, permissions, user_roles, role_permissions) e RLS estão ativos no banco real. |
| 31/07/2026 | Módulo 1 / Bloco B concluído: models SQLAlchemy, Alembic configurado (async), primeira migração com RLS (`FORCE ROW LEVEL SECURITY` em `users` e `roles`), `SqlAlchemyUserRepository` implementando a interface do domínio. Limitação conhecida registrada: `user_roles`/`role_permissions` não têm RLS direto, apenas proteção indireta via JOIN — revisitar no Bloco F (testes de isolamento). Nova convenção adotada: migrações Alembic numeradas sequencialmente (`0001_`, `0002_...`), não hash aleatório. |
| 31/07/2026 | Problema de design encontrado ao planejar o Bloco E: `FORCE ROW LEVEL SECURITY` em `users`/`roles` bloquearia os fluxos de registro, login e refresh, que precisam tocar essas tabelas ANTES de existir qualquer autenticação prévia que sete o contexto de tenant. Corrigido adicionando a porta `TenantContextSetter` (application/auth/ports.py) — cada caso de uso agora declara explicitamente o tenant ativo no momento em que o descobre (registro: logo após criar o tenant; login: logo após validar o tenant informado; refresh: logo após decodificar o token). Implementação real em `infrastructure/database/tenant_context_setter.py`. Validado com testes funcionais usando fakes. |
| 31/07/2026 | Módulo 1 / Bloco C concluído: casos de uso `RegisterTenantUseCase`, `LoginUseCase`, `RefreshTokenUseCase` (com rotação de refresh token), portas `PasswordHasher`/`TokenService`/`RefreshTokenBlocklist`, `TenantRepository` (lacuna do Bloco A preenchida). Validado com testes funcionais usando fakes em memória (sem infraestrutura real). |
| 31/07/2026 | Módulo 1 / Bloco D concluído: implementações reais das portas de segurança — `BcryptPasswordHasher`, `JwtTokenService` (access/refresh diferenciados por campo `type`), `RedisRefreshTokenBlocklist` (TTL automático), `SqlAlchemyTenantRepository`. Novo componente de infraestrutura: cliente Redis compartilhado (`infrastructure/cache/redis_client.py`). |
| 31/07/2026 | Módulo 1 / Bloco E concluído: schemas Pydantic, `dependencies.py` (composition root da API), handlers globais de exceção (`ApplicationError`/`DomainError` → HTTP), router de auth (`/register`, `/login`, `/refresh`, `/me`). Nova dependência adicionada: `email-validator` (necessária para `EmailStr`). Decisão registrada: commit da transação acontece no router, não no repository/caso de uso (revisitar com Unit of Work se necessário). |
| 31/07/2026 | Módulo 1 / Bloco F concluído: testes de isolamento de tenant em nível de banco (RLS: SELECT cru sem filtro bloqueado, fail-closed sem contexto, INSERT com tenant_id divergente rejeitado) e testes de fluxo de autenticação via API. Corrigido gap no CI (`alembic upgrade head` faltava antes do `pytest`) e erro de plugin de teste (marcador de `pytest-anyio` usado por engano; projeto usa `pytest-asyncio`). |
| 31/07/2026 | Bug 6 encontrado pelo usuário ao rodar `pytest` dentro do container: `Dockerfile` só instalava dependências de produção, nunca o grupo `[dev]` (pytest, ruff, mypy) — container local não tinha `pytest` disponível. Corrigido adicionando um terceiro estágio `dev` no `Dockerfile` (instala `.[dev]` por cima da imagem de runtime) e apontando o `docker-compose.yml` para esse estágio (`target: dev`). A imagem de produção real (stage `runtime`) continua sem essas ferramentas. |
| 31/07/2026 | Bug 7 encontrado pelo usuário ao rodar `pytest` (0 testes coletados): a pasta `tests/` nunca era copiada para a imagem Docker nem montada como bind mount — só existia no host. Corrigido copiando `./tests` no estágio `dev` do `Dockerfile` e adicionando bind mount `./backend/tests:/app/tests` no `docker-compose.yml`, consistente com o padrão já usado para `src/` e `alembic/`. |
| 31/07/2026 | Bug 8 encontrado pelo usuário ao rodar a suíte de testes pela primeira vez: `SET LOCAL app.current_tenant_id = :tenant_id` falhava com erro de sintaxe — PostgreSQL não aceita bind parameters (`$1`) dentro de comandos `SET`/`SET LOCAL`, só em statements normais (SELECT/INSERT/etc). Corrigido usando a função `set_config('app.current_tenant_id', :valor, true)` em `set_tenant_context`/`clear_tenant_context` (infrastructure/database/session.py) — mesma semântica de escopo transacional (`is_local=true` = `SET LOCAL`), mas parametrizável corretamente. Nenhuma mudança necessária na policy de RLS (ela lê via `current_setting`, que é compatível com `set_config`). |
| 31/07/2026 | Bug 9 encontrado no mesmo log: testes falhando com "Future attached to a different loop" — `pytest-asyncio` cria um event loop novo por função de teste por padrão, mas o `engine` do SQLAlchemy é compartilhado com um pool de conexões `asyncpg` presas ao loop em que foram criadas. Corrigido com `asyncio_default_fixture_loop_scope = "session"` no `pyproject.toml`, fazendo toda a sessão de testes compartilhar um único event loop. |
| 31/07/2026 | Limpeza: `status.HTTP_422_UNPROCESSABLE_ENTITY` (deprecado no Starlette) substituído por `HTTP_422_UNPROCESSABLE_CONTENT` em `error_handlers.py`, mesmo código HTTP 422. |
| 31/07/2026 | Bug 10 encontrado pelo usuário: `ValueError: password cannot be longer than 72 bytes` ao hashear senhas curtas normais — causa real era incompatibilidade entre `passlib` (sem atualização há anos) e `bcrypt>=4.1` (que removeu o atributo `__about__` que o passlib usa para detectar a versão do backend, disparando um fallback de auto-diagnóstico que quebra). Corrigido fixando `bcrypt>=4.0.1,<4.1` explicitamente no `pyproject.toml`. |
| 31/07/2026 | Bug 11 (erro meu de instrução, não de código): disse ao usuário para rodar só `docker compose restart backend` após a correção do event loop (Bug 9), mas essa correção estava no `pyproject.toml`, que NÃO está no bind mount do `docker-compose.yml` (só `src/`, `alembic/`, `tests/` estão) — só é aplicado com `--build`. Lição registrada para o projeto: qualquer mudança em `pyproject.toml` (dependências ou configuração de ferramentas como pytest/ruff/mypy) sempre exige rebuild da imagem, nunca só restart. |
| 31/07/2026 | Bug 12: correção do Bug 9 (event loop) foi incompleta — `pytest-asyncio` 1.x separa `asyncio_default_fixture_loop_scope` de `asyncio_default_test_loop_scope`; só o primeiro tinha sido configurado. Corrigido adicionando os dois com valor `"session"`. |
| 31/07/2026 | Bug 13: como efeito colateral do Bug 12, testes que falhavam no meio de uma transação deixavam conexões "sujas" no pool de produção compartilhado, causando um falso positivo de vazamento de dados entre tenants num teste (`AssertionError: VAZAMENTO`) — não era o RLS falhando, era estado residual de conexão reaproveitada. Corrigido criando uma engine de teste SEPARADA da de produção, com `NullPool` (cada conexão é sempre nova, nunca reaproveitada) e um `app.dependency_overrides` trocando `get_db_session` só durante os testes. A engine de produção não foi alterada. |
| 31/07/2026 | **Bug 14 (o mais importante do módulo):** com os bugs de infraestrutura de teste resolvidos, os testes de RLS finalmente rodaram "de verdade" e revelaram vazamento real — não por policy errada, mas porque o usuário de banco da aplicação (`POSTGRES_USER`, criado como superuser pela imagem oficial do Postgres) **sempre ignora RLS**, mesmo com `FORCE ROW LEVEL SECURITY` (regra do próprio PostgreSQL, não contornável via policy). Corrigido com ADR-008: novo usuário `campanhaos_app` sem privilégio de superuser (criado pela migração `0002_create_app_role`), usado pela aplicação em runtime; o superuser original passa a ser usado só para migrações (`MIGRATION_DATABASE_URL`, novo campo em `Settings`). Todos os `.env`, CI e README atualizados com as duas URLs. |
| 01/08/2026 | Bug 15 (erro meu de instrução): disse ao usuário para usar `docker compose restart backend` depois de editar o `.env` com as variáveis novas do ADR-008 — mas `restart` reinicia o processo do container existente, não relê o `.env` nem recria o container. É preciso `docker compose up -d`, que detecta mudança de configuração/ambiente e recria o container. Regra adicionada às convenções do projeto. |
| 01/08/2026 | Bug 16: como consequência do Bug 15, a migração `0002_create_app_role` rodou pela primeira vez ANTES do `.env` estar com o `APP_DB_PASSWORD` correto, criando o usuário `campanhaos_app` com uma senha diferente da que ficou em `DATABASE_URL` depois. Como o Alembic nunca reexecuta uma migração já aplicada, corrigir o `.env` sozinho não resolveu. Corrigido com uma nova migração (`0003_sync_app_role_password`, nunca editamos uma migração já aplicada) que sincroniza a senha do usuário para o valor atual de `APP_DB_PASSWORD`. |
| 01/08/2026 | Bug 17: erro de senha persistiu mesmo após `docker compose up -d` e a migração 0003 — suspeita: `docker compose up -d` nem sempre detecta mudança de CONTEÚDO de um `env_file` referenciado (só detecta com confiança mudança no caminho do arquivo), então o container `backend` pode ter continuado com as variáveis de ambiente antigas. Correção recomendada: `docker compose up -d --force-recreate backend`, com passo de diagnóstico (`docker compose exec backend sh -c "echo $VAR"`) para confirmar antes de assumir que resolveu. Convenção do projeto atualizada. |
| 01/08/2026 | Bug 18: após confirmar que o `.env` estava correto dentro do container, o erro de senha voltou a aparecer — mas agora para o usuário `campanhaos` (migração/superuser), não mais `campanhaos_app`. Causa: a imagem oficial do PostgreSQL só aplica `POSTGRES_USER`/`POSTGRES_PASSWORD` na criação INICIAL do volume de dados — mudanças posteriores nessas variáveis no `.env` não alteram a senha já gravada no Postgres. Corrigido resetando o volume local (`docker compose down -v` + `up -d --build`), aceitável por ser ambiente de desenvolvimento sem dado real. Lição registrada: se `POSTGRES_PASSWORD` precisar mudar depois que o volume já existe, é preciso `ALTER USER` manual via psql/Adminer, ou resetar o volume — simplesmente editar o `.env` não é suficiente. |
| 01/08/2026 | **Módulo 1 (Tenants + Auth) CONCLUÍDO.** Validação final do usuário: `pytest -v --cov=src` → 10 passed, 87% de cobertura (acima da meta de 80%, ADR-006). Os 3 testes de RLS de baixo nível (`test_tenant_isolation.py`) confirmam ativamente o isolamento entre tenants em ambiente real. Módulo marcado ✅ no mapa de módulos (seção 5). Próximo módulo: CRM de Eleitores. |
| 01/08/2026 | Bug 19 (Módulo 2, Bloco E): `Voter.soft_delete()` gera `deleted_at` com `datetime.now(UTC)` (timezone-aware), mas a coluna no banco era `TIMESTAMP WITHOUT TIME ZONE` — `asyncpg` rejeitou o valor (`DataError: invalid input for query argument`). Causa raiz: todas as colunas de timestamp do projeto (`tenants`, `users`, `roles`, `voters`) tinham esse mesmo problema adormecido, só não tinha sido acionado ainda porque `created_at`/`updated_at` sempre vinham de `server_default=func.now()` (gerado pelo banco), nunca de Python. Corrigido na causa raiz: `TimestampMixin` e `VoterModel.deleted_at` agora usam `DateTime(timezone=True)` (`timestamptz`), e a migração `0005_use_timestamptz` converte as colunas já existentes no banco. |
| 01/08/2026 | **Módulo 2 (CRM de Eleitores) CONCLUÍDO.** Validação final do usuário: `pytest -v --cov=src` → 20 passed, 87% de cobertura. Módulo marcado ✅ no mapa de módulos (seção 5). Próximo módulo: Lideranças. |
| 01/08/2026 | Módulo 3 (Lideranças) desenvolvido: CRUD completo de `Leadership` + associação opcional `Voter.leadership_id`, com validação cross-entity (liderança precisa existir e pertencer ao mesmo tenant) e sentinela de 3 camadas (domínio → aplicação → API, via `request.model_fields_set`) para distinguir "não mexer" de "remover associação" num campo nullable. Migrações `0006_create_leaderships` e `0007_add_leadership_id_to_voters`. |
| 01/08/2026 | **Módulo 3 (Lideranças) CONCLUÍDO.** Validação final do usuário: `pytest -v --cov=src` → 34 passed, 87% de cobertura — nenhum bug novo encontrado no processo, primeira vez isso acontece desde o Módulo 0. Módulo marcado ✅ no mapa de módulos (seção 5). Próximo módulo: Agenda. |
| 01/08/2026 | Módulo 4 (Agenda) desenvolvido: CRUD completo de `Event` (tipo, status, validação de período), associação opcional com Eleitor e Liderança (dois sentinelas independentes), responsável opcional (default: usuário autenticado). Migração `0008_create_events`. |
| 01/08/2026 | **Módulo 4 (Agenda) CONCLUÍDO.** Validação final do usuário: `pytest -v --cov=src` → 49 passed, 86% de cobertura — segundo módulo seguido sem nenhum bug novo. Módulo marcado ✅ no mapa de módulos (seção 5). Próximo módulo: Frontend base (Módulo 5) — primeiro módulo de frontend do projeto, vai exigir setup novo (React/Vite/TailwindCSS, ainda não iniciado). |
| 05/08/2026 | Módulo 5 (Frontend base) iniciado: setup do zero de React 18 + Vite + TypeScript (strict) + TailwindCSS v3 + Shadcn UI (componentes copiados, não instalados via npm) + React Router + React Query + Vitest/RTL. ADR novo implícito: JWT access token em memória (nunca persistido) + refresh token em `sessionStorage` — trade-off de segurança documentado no código (solução ideal seria cookie `httpOnly`, exigiria mudança no backend, fora de escopo). Limitação conhecida: login exige `tenant_id` (UUID) digitado manualmente — não existe endpoint de busca de campanha por nome ainda. |
| 05/08/2026 | Durante o Bloco A, `tsc` (rodado localmente, sem `npm install`) encontrou 2 bugs reais de configuração antes mesmo da validação do usuário: `tsconfig.node.json` sem `composite: true` (exigido por ser projeto referenciado, conflitava com `noEmit`), e `baseUrl` deprecado no modo `moduleResolution: bundler` (corrigido com `ignoreDeprecations: "6.0"`). |
| 05/08/2026 | Bug encontrado pelo usuário ao rodar `npm test`: teste "mostra erro e não chama onSubmit quando o nome está vazio" falhou — o atributo HTML `required` no campo Nome (`VoterForm.tsx`) fazia o navegador/jsdom bloquear o envio do formulário via validação nativa ANTES do evento `submit` disparar, impedindo a validação customizada em JavaScript de rodar. Corrigido removendo o `required` nativo (a validação customizada já cobre o caso, com mensagem em português consistente com o resto do formulário). |
| 05/08/2026 | **Módulo 5 (Frontend base) CONCLUÍDO.** Validação final do usuário: `npm test` → 11 passed, e teste manual completo no navegador (registro de tenant via Swagger, login real, CRUD de eleitores end-to-end conversando com o backend real). Módulo marcado ✅ no mapa de módulos (seção 5). Próximo módulo: Financeiro básico. |
| 05/08/2026 | Módulo 6 (Financeiro básico) desenvolvido: CRUD de `FinanceTransaction` com `Decimal`/`NUMERIC(12,2)` (nunca float), `amount` sempre positivo com sinal derivado do `type`, resumo (totais + saldo) calculado via agregação SQL respeitando filtros da listagem, `CHECK CONSTRAINT` no banco como segunda camada de defesa. Migração `0009_create_finance_transactions`. |
| 05/08/2026 | **Módulo 6 (Financeiro básico) CONCLUÍDO.** Validação final do usuário: `pytest -v --cov=src` → 62 passed, 86% de cobertura — nenhum bug novo encontrado nesta rodada. Módulo marcado ✅ no mapa de módulos (seção 5). Próximo módulo: Billing + painel super-admin. |
| 06/08/2026 | Módulo 7 (Billing + Painel Super-Admin) desenvolvido: `Plan`/`Subscription`/`PlatformAdmin`, autenticação de super-admin separada (JWT com namespace de tipo distinto — ver ADR-009), gestão de tenants, CRUD de planos, atribuição de assinatura sem bypass de RLS. `TenantRepository` (Módulo 1) estendido com `list_paginated`. Migrações `0010`-`0012`. |
| 06/08/2026 | **Decisão de negócio registrada (ADR-009, ADR-010):** usuário sob pressão de prazo real — piloto fechado com 1-2 campanhas reais, uso em eleição em andamento, dado real de eleitor. Escopo do Módulo 7 reduzido conscientemente (sem bypass de RLS, sem gateway de pagamento real). Risco de compliance TSE/LGPD sinalizado: prestação de contas oficial das Eleições 2026 é via **Conta+JE** (TSE), não o módulo Financeiro do CampanhaOS. Roadmap reorganizado: Módulo de Deploy e frontend de Lideranças/Agenda/Financeiro inseridos como próximos passos, antes do Módulo 8 (IA) e 9+ (WhatsApp etc.), que ficam para depois do piloto. |
| 06/08/2026 | **Módulo 7 (Billing + Painel Super-Admin) CONCLUÍDO.** Validação final do usuário: `pytest -v --cov=src` → 84 passed, 86% de cobertura. Único problema no processo: confusão de nomes de arquivo repetidos entre pastas (`admin_auth.py` em `routers/` e `schemas/`) — resolvido em 2 rodadas, sem bug de lógica. Módulo marcado ✅ no mapa de módulos (seção 5). Próximo: Módulo de Deploy. |
| 06/08/2026 | Módulo de Deploy desenvolvido: decisão de hospedagem (ADR-011, Railway + Vercel, Supabase descartado por inviabilidade técnica para hospedar o backend). Bug real corrigido (CORS fechado em produção desde o Módulo 0, nunca percebido). Sentry inicializado pela primeira vez. `Dockerfile.production`/`railway.json` (contornando limitação do Railway de não suportar target de Dockerfile multi-stage). `vercel.json`. Backup via GitHub Actions agendado. `RUNBOOK-DEPLOY.md` completo. **Módulo diferente de todos os anteriores: sem validação de execução real possível por Claude — 100% da validação é do usuário, seguindo o runbook.** |

---

## 9. Próximo Passo

**Piloto no ar, com o comercial também avançando — proposta enviada pra um segundo candidato.** Sistema validado ponta a ponta em produção: autocadastro público, autocadastro por liderança específica, anexo financeiro, painel com estatísticas completas (gênero, idade, crescimento, meta, ranking de liderança). Antes de seguir:
1. Salvar a versão atual deste documento.
2. Se o segundo candidato (proposta comercial já enviada) fechar negócio: criar o tenant novo dele via `POST /auth/register`, e configurar WhatsApp (Twilio) separadamente pra essa campanha, já que cada uma precisa do próprio número/sandbox.

**Correção de nota antiga**: o item "Frontend de Lideranças/Agenda/Financeiro ainda falta" (que aparecia aqui antes) está desatualizado — todas essas telas já foram construídas e estão em uso normal há várias sessões.

**Outras opções em aberto (nenhuma é bloqueante):**
1. **Mapa mental de relacionamentos** (lideranças ↔ eleitores) — já desenhado, não iniciado
2. Módulos 8 (IA) e 9+ (funcionalidades da Fase 1 ainda não quebradas em módulos)
3. WhatsApp com número de produção (sair do Sandbox do Twilio) — precisa de verificação de negócio na Meta
4. **Lição de processo pra sessões futuras**: essa sessão teve MUITO arquivo "esquecido" na cópia entre o chat e os ambientes reais (Codespace/PC local), além de confusão de sincronização Git entre os dois ambientes. Vale considerar: (a) usar só UM ambiente por sessão de trabalho, ou (b) sempre rodar `git pull` logo ao trocar de ambiente, antes de aplicar qualquer arquivo novo.
