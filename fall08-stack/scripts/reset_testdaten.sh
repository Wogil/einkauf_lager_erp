#!/usr/bin/env bash
# Setzt nur die Daten des Prüfdienstes zurück (Vorgänge, Vorschläge, Entscheidungen, Mail-Protokoll).
# WAVE-Daten, Register und n8n bleiben erhalten – danach können dieselben .eml erneut eingespielt werden.
set -euo pipefail
cd "$(dirname "$0")/.."
docker compose exec -T db psql -U postgres -d vosskamp -v ON_ERROR_STOP=1 -c \
  "TRUNCATE app.protokoll, app.entscheidung, app.vorschlag, app.rechnung, app.dokument, app.vorgang, app.mail_log CASCADE;"
echo "Prüfdienst-Daten zurückgesetzt. Mailpit leeren: http://localhost:8025 → Delete all"
