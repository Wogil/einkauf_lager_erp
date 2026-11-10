#!/bin/sh
# Importiert die Workflows aus /workflows, veröffentlicht sie und startet n8n.
# Ein erneuter Import überschreibt die Workflows mit gleicher ID (Stand aus dem Repo gilt).
set -e
n8n import:workflow --separate --input=/workflows
for f in /workflows/*.json; do
  id=$(node -e "process.stdout.write(require(process.argv[1]).id)" "$f")
  n8n publish:workflow --id="$id" || echo "Hinweis: $id konnte nicht veröffentlicht werden"
done
exec n8n start
