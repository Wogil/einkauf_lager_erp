#!/usr/bin/env bash
# Lädt die Referenzdaten: ArchivPlus-Index und Handelsregister-Index.
(
  set -eo pipefail
  export PGUSER="$POSTGRES_USER" PGDATABASE="$POSTGRES_DB"
  echo "[init] Lade ArchivPlus-Index …"
  psql -v ON_ERROR_STOP=1 -q -c "\\copy ref.archivplus_index FROM '/seed/archivplus/ArchivPlus_Index_Eingangsrechnungen.csv' WITH (FORMAT csv, HEADER true, DELIMITER ';', NULL '')"
  echo "[init] Lade Handelsregister-Index …"
  psql -v ON_ERROR_STOP=1 -q -c "\\copy ref.register FROM '/seed/register/index.csv' WITH (FORMAT csv, HEADER true, NULL '')"
  echo "[init] Referenzdaten geladen."
)
