#!/usr/bin/env bash
# Export der Kennzahlen-Rohdaten (GitHub #44): eine Zeile je Rechnung, als CSV (Semikolon) für Excel.
# Grundlage für die Kennzahlen der Evaluation (B1, C1, D1). Berechnet selbst keine Kennzahlen.
#
# Aufruf (aus fall08-stack/, Stack läuft):
#   bash scripts/kpi_export.sh <lauf_id> <variante>      z. B.  bash scripts/kpi_export.sh B1-01 B1
# Ergebnis: exports/kpi_<lauf_id>.csv
#
# WICHTIG: Vor scripts/reset_testdaten.sh exportieren – das Zurücksetzen löscht alle Ergebnisse.
#
# Weg A/B/C nach Kriterienkatalog Fall 08:
#   C = mindestens ein Befund "kritisch" oder eine der verschärften Warnungen (Absender, Bank, Anweisung im Beleg)
#   B = sonst mindestens eine "warnung" oder Bruttobetrag über 10.000 € (Agent prüft zusätzlich)
#   A = nur Hinweise ("info") oder keine Befunde
# Tokens und Kosten des Agenten bleiben leer, bis geklärt ist, was SRW je Job liefert.
set -euo pipefail
cd "$(dirname "$0")/.."

LAUF="${1:?Lauf-ID fehlt, z. B. B1-01}"
VARIANTE="${2:?Variante fehlt: B1, C1 oder D1}"
mkdir -p exports
ZIEL="exports/kpi_${LAUF}.csv"

printf '\xEF\xBB\xBF' > "$ZIEL"   # BOM, damit Excel die Umlaute richtig anzeigt
docker compose exec -T db psql -U postgres -d vosskamp -q -v ON_ERROR_STOP=1 \
  -v lauf="$LAUF" -v variante="$VARIANTE" >> "$ZIEL" <<'SQL'
COPY (
WITH b AS (
    SELECT r.id, x->>'code' AS code, x->>'schwere' AS schwere
    FROM app.rechnung r, jsonb_array_elements(r.pruefung->'befunde') x
),
v AS (SELECT DISTINCT ON (rechnung_id) * FROM app.vorschlag    ORDER BY rechnung_id, erstellt_am DESC),
e AS (SELECT DISTINCT ON (rechnung_id) * FROM app.entscheidung ORDER BY rechnung_id, erstellt_am DESC)
SELECT
    :'lauf'                                              AS lauf_id,
    :'variante'                                          AS variante,
    r.pruefung->>'regelversion'                          AS regelversion,
    r.id                                                 AS rechnung_id,
    r.pruefung->'zuordnung'->>'lieferanten_nr'           AS lieferant_nr,
    r.extrakt->>'rechnungsnr'                            AS rechnungsnr,
    r.extrakt->>'format'                                 AS format,
    replace(r.extrakt->>'brutto', '.', ',')              AS brutto,
    (SELECT string_agg(code, ',' ORDER BY code) FROM b WHERE b.id = r.id) AS befund_codes,
    CASE
        WHEN EXISTS (SELECT 1 FROM b WHERE b.id = r.id AND (b.schwere = 'kritisch' OR b.code IN
                ('BANK_BLZ_WIDERSPRUCH', 'ABSENDER_DOMAIN_FREMD', 'REPLY_TO_ABWEICHEND',
                 'BANKAENDERUNG_MAIL_VORHER', 'ANWEISUNG_IM_BELEG'))) THEN 'C'
        WHEN EXISTS (SELECT 1 FROM b WHERE b.id = r.id AND b.schwere = 'warnung')
             OR coalesce((r.extrakt->>'brutto')::numeric, 0) > 10000 THEN 'B'
        ELSE 'A'
    END                                                  AS weg,
    r.pruefung->'regelvorschlag'->>'entscheidung'        AS regelvorschlag,
    v.entscheidung                                       AS vorschlag,
    v.quelle                                             AS vorschlag_quelle,
    (vg.srw_job_id IS NOT NULL AND v.quelle = 'regeln')  AS rueckfall,
    CASE WHEN v.id IS NULL THEN NULL ELSE NOT EXISTS (
        SELECT 1 FROM jsonb_array_elements(v.begruendungen) g
        WHERE g->>'code' IS DISTINCT FROM 'OK'
          AND (g->>'beleg' IS NULL OR g->>'bezug' IS NULL OR g->>'betrag' IS NULL)) END
                                                         AS mit_beleg_bezug_betrag,
    v.freigabe->>'stufe'                                 AS freigabestufe,
    v.kontierung->0->>'sachkonto'                        AS sachkonto,
    v.kontierung->0->>'kostenstelle'                     AS kostenstelle,
    v.skonto->>'freigabe_spaetestens'                    AS freigabe_spaetestens,
    vg.erstellt_am                                       AS t_start,
    v.erstellt_am                                        AS t_vorschlag,
    round(extract(epoch FROM v.erstellt_am - vg.erstellt_am)) AS dauer_s,
    vg.srw_job_id                                        AS srw_job_id,
    NULL                                                 AS tokens_ein,
    NULL                                                 AS tokens_aus,
    NULL                                                 AS kosten_eur,
    e.aktion                                             AS mensch_aktion,
    e.erstellt_am                                        AS mensch_zeitpunkt,
    e.kommentar                                          AS mensch_kommentar
FROM app.rechnung r
JOIN app.vorgang vg   ON vg.id = r.vorgang_id
LEFT JOIN v           ON v.rechnung_id = r.id
LEFT JOIN e           ON e.rechnung_id = r.id
ORDER BY vg.erstellt_am, r.erstellt_am
) TO STDOUT WITH (FORMAT csv, HEADER, DELIMITER ';');
SQL

ZEILEN=$(($(wc -l < "$ZIEL") - 1))
echo "Export: $ZIEL ($ZEILEN Rechnungen, Lauf $LAUF, Variante $VARIANTE)"
