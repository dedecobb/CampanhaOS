#!/usr/bin/env bash
# Backup do PostgreSQL de produção via pg_dump.
#
# Uso manual:
#   MIGRATION_DATABASE_URL="postgresql://..." ./scripts/backup_database.sh
#
# O arquivo gerado usa o formato "custom" do pg_dump (-Fc), que é
# comprimido e permite restauração seletiva (tabela por tabela, se
# necessário) — mais flexível que um dump de texto puro (.sql).
#
# Usa MIGRATION_DATABASE_URL (usuário superuser), não DATABASE_URL —
# precisa de privilégio para ler TODAS as tabelas de TODOS os tenants,
# o que o usuário de aplicação (campanhaos_app) não tem motivo pra ter.

set -euo pipefail

if [ -z "${MIGRATION_DATABASE_URL:-}" ]; then
    echo "Erro: variável MIGRATION_DATABASE_URL não definida." >&2
    exit 1
fi

# pg_dump não entende o driver "+asyncpg" do SQLAlchemy — remove esse
# sufixo antes de passar a URL adiante.
PG_DUMP_URL="${MIGRATION_DATABASE_URL/postgresql+asyncpg:\/\//postgresql://}"

TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
OUTPUT_FILE="campanhaos_backup_${TIMESTAMP}.dump"

echo "Iniciando backup para ${OUTPUT_FILE}..."
pg_dump "${PG_DUMP_URL}" -Fc -f "${OUTPUT_FILE}"
echo "Backup concluído: ${OUTPUT_FILE} ($(du -h "${OUTPUT_FILE}" | cut -f1))"
