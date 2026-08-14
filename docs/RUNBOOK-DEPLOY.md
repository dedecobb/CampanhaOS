# Runbook de Deploy — CampanhaOS (Piloto Railway + Vercel)

> Siga na ordem. Cada passo indica o que fazer e como confirmar que deu certo antes de ir pro próximo.

---

## 0. Pré-requisitos

- [ ] Conta no [Railway](https://railway.app) (pode logar com GitHub)
- [ ] Conta no [Vercel](https://vercel.com) (pode logar com GitHub)
- [ ] Repositório já no GitHub, com os módulos 0-7 commitados (incluindo os arquivos deste módulo: `Dockerfile.production`, `railway.json`, `vercel.json`, workflow de backup)

---

## 1. Gerar os segredos de produção (nunca reuse os valores de dev)

Roda isso no seu terminal local (não precisa ser dentro do Docker) pra gerar 3 valores aleatórios fortes — guarda o resultado, você vai usar nos próximos passos:

```powershell
python -c "import secrets; print('JWT_SECRET_KEY=', secrets.token_urlsafe(64))"
python -c "import secrets; print('APP_DB_PASSWORD=', secrets.token_urlsafe(32))"
```

⚠️ **Nunca** reutilize o `JWT_SECRET_KEY` ou `APP_DB_PASSWORD` que você usa localmente — são ambientes diferentes, segredos diferentes.

---

## 2. Criar o projeto no Railway e provisionar Postgres + Redis

1. No painel do Railway, **New Project** → **Empty Project**.
2. Dentro do projeto: **+ New** → **Database** → **Add PostgreSQL**.
3. **+ New** → **Database** → **Add Redis**.
4. Clica no serviço Postgres → aba **Variables** → confirma que existe algo como `DATABASE_URL` (formato `postgresql://usuario:senha@host:porta/banco`) — vamos usar os componentes dela no próximo passo.

**Checkpoint:** você deve ver 2 serviços no canvas do projeto: Postgres e Redis, os dois com bolinha verde ("running").

---

## 3. Deploy do backend

1. No mesmo projeto Railway: **+ New** → **GitHub Repo** → seleciona seu repositório.
2. Nas configurações do novo serviço (aba **Settings**):
   - **Root Directory**: `backend`
   - Confirma que ele detectou o `railway.json` (aba **Settings** → **Build**, deve mostrar "Dockerfile" como builder, apontando pra `Dockerfile.production`)
3. Aba **Variables** do serviço de backend — adiciona TODAS estas (usando a sintaxe de referência do Railway, `${{Postgres.VARIAVEL}}`, pra puxar os valores do serviço Postgres/Redis automaticamente, sem copiar/colar manualmente):

   ```
   ENVIRONMENT=production
   DEBUG=false

   # Superuser do Postgres (usado só pra migração) — Railway já injeta os
   # componentes individuais do Postgres; construímos a URL asyncpg com eles.
   MIGRATION_DATABASE_URL=postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}

   # Usuário de aplicação (campanhaos_app) — criado pela migração 0002 na
   # primeira vez que o container sobe. A senha é a que você gerou no Passo 1.
   APP_DB_PASSWORD=<cole o APP_DB_PASSWORD gerado no Passo 1>
   DATABASE_URL=postgresql+asyncpg://campanhaos_app:<mesma senha do APP_DB_PASSWORD>@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}

   REDIS_URL=${{Redis.REDIS_URL}}

   JWT_SECRET_KEY=<cole o JWT_SECRET_KEY gerado no Passo 1>
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=15
   REFRESH_TOKEN_EXPIRE_DAYS=7

   # Preenche no Passo 6, depois que o frontend existir — deixa vazio por
   # enquanto (CORS fica fechado até lá, sem problema, ninguém usa ainda).
   FRONTEND_URL=
   ```

4. Clica em **Deploy**.

**Checkpoint — validação real:** acompanha os logs de build/deploy na aba **Deployments**. Você deve ver, nessa ordem:
```
INFO  [alembic.runtime.migration] Running upgrade ... -> 0012_create_platform_admins ...
INFO:     Application startup complete.
```

⚠️ **Se der erro na migração** (ex: `permission denied to create role`): significa que o usuário do Postgres do Railway não tem privilégio pra `CREATE ROLE` — isso é uma possibilidade real que eu não consigo confirmar sem testar de verdade. Se acontecer, me manda o log completo do erro que a gente resolve juntos, provavelmente com uma pequena mudança de abordagem pra esse ambiente específico.

Depois do deploy, o Railway te dá uma URL pública (aba **Settings** → **Networking** → **Generate Domain**), algo como `campanhaos-backend-production.up.railway.app`.

**Confirma rodando:**
```powershell
curl https://SEU-BACKEND.up.railway.app/api/v1/health
# Esperado: {"status":"ok"}
```

---

## 4. Criar o primeiro super-admin em produção

Na aba do serviço de backend no Railway, tem uma opção de rodar comando único (CLI do Railway, ou terminal integrado no painel, dependendo da versão da interface). O comando é o mesmo que você já usa localmente:

```
python -m scripts.create_platform_admin --name "Seu Nome" --email "voce@campanhaos.com" --password "uma-senha-forte-de-producao"
```

Se preferir usar a CLI do Railway do seu computador:
```powershell
railway login
railway link   # conecta ao projeto certo
railway run python -m scripts.create_platform_admin --name "Seu Nome" --email "voce@campanhaos.com" --password "uma-senha-forte-de-producao"
```

**Checkpoint:** deve imprimir `Super-admin criado com sucesso: ...`.

---

## 5. Deploy do frontend no Vercel

1. No painel do Vercel: **Add New** → **Project** → seleciona o mesmo repositório GitHub.
2. **Root Directory**: `frontend`
3. Framework preset: deve detectar **Vite** automaticamente.
4. **Environment Variables** → adiciona:
   ```
   VITE_API_URL=https://SEU-BACKEND.up.railway.app/api/v1
   ```
   (a mesma URL que você confirmou funcionando no Passo 3)
5. **Deploy**.

**Checkpoint:** o Vercel te dá uma URL tipo `campanhaos.vercel.app`. Abre ela — deve cair na tela de login.

---

## 6. Fechar o CORS (voltar no Railway)

Agora que o frontend tem uma URL real:

1. Volta no serviço de **backend** no Railway → **Variables**.
2. Atualiza `FRONTEND_URL` com a URL do Vercel: `https://campanhaos.vercel.app` (sem barra no final).
3. O Railway faz redeploy automático ao salvar uma variável.

**Checkpoint:** tenta logar pelo frontend de verdade (você já tem um super-admin, mas login de USUÁRIO precisa de um tenant registrado — usa o Swagger do backend em produção, `https://SEU-BACKEND.up.railway.app/api/v1/docs`, pra registrar um tenant de teste, depois loga no frontend com esses dados).

---

## 7. Observabilidade (Sentry) — opcional, mas recomendado

1. Cria uma conta grátis em [sentry.io](https://sentry.io), um projeto do tipo "FastAPI"/Python.
2. Copia o DSN que eles fornecem.
3. Railway → backend → Variables → `SENTRY_DSN=<o DSN copiado>`.

**Checkpoint:** força um erro de propósito (ex: chama um endpoint com dado inválido) e confirma que aparece no painel do Sentry em alguns segundos.

---

## 8. Backup automatizado (GitHub Actions)

1. No GitHub, vai em **Settings** → **Secrets and variables** → **Actions** → **New repository secret**.
2. Nome: `PRODUCTION_MIGRATION_DATABASE_URL`. Valor: a mesma `MIGRATION_DATABASE_URL` que você usou no Passo 3 (com os valores reais resolvidos, não a sintaxe `${{...}}` do Railway — copia o valor final da aba Variables do Postgres).
3. Testa manualmente: GitHub → aba **Actions** → "Backup do Banco de Dados (Produção)" → **Run workflow**.

**Checkpoint:** o workflow deve rodar verde, e um artefato `campanhaos-backup-...` deve aparecer disponível pra download.

---

## 9. Teste end-to-end completo, antes de convidar qualquer campanha

- [ ] Registrar um tenant de teste via frontend/Swagger
- [ ] Login funcionando
- [ ] Criar/editar/excluir um eleitor pelo frontend
- [ ] Criar uma liderança, um evento, um lançamento financeiro (via Swagger, já que essas telas ainda não existem no frontend — próximo módulo)
- [ ] Login de super-admin funcionando, consegue listar tenants
- [ ] `/api/v1/health` respondendo
- [ ] Sentry capturando erro de teste (se configurado)

## 10. Antes de convidar as campanhas de verdade

- [ ] Deixar claro para os usuários: **Financeiro é controle interno**, prestação de contas oficial é via Conta+JE (TSE) — ver ADR-010 no documento fonte da verdade
- [ ] Confirmar que você (ou alguém) vai acompanhar de perto os primeiros dias (é um piloto, bugs de uso real são esperados)

---

## Troubleshooting rápido

| Sintoma | Causa provável |
|---|---|
| Erro de CORS no navegador (console do frontend) | `FRONTEND_URL` não configurada, ou configurada com barra no final, ou domínio errado |
| `502 Bad Gateway` no backend | Container ainda subindo, ou crashou — olha os logs do Railway |
| Login funciona no Swagger mas não no frontend | Confirma `VITE_API_URL` no Vercel — lembra que precisa de **novo build** pra pegar mudança (ver Bloco C) |
| Erro de permissão na migração (`CREATE ROLE`) | Me manda o log — provavelmente precisa de um ajuste específico pro Postgres gerenciado do Railway |
