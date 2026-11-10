#!/usr/bin/env bash
# Lädt den WAVE-Export mit dem Original-Ladeskript des Kunden (companies/a_vosskamp/erp/load_postgres.sh).
# Wird vom Postgres-Container nur beim allerersten Start ausgeführt (leeres Volume).
# Läuft in einer Subshell, damit es auch funktioniert, wenn der Container das Skript "sourct".
(
  set -eo pipefail
  echo "[init] Lade WAVE-Export aus /seed/erp …"
  cd /seed/erp
  PGUSER="$POSTGRES_USER" PGDATABASE="$POSTGRES_DB" bash ./load_postgres.sh
)
