-- Tabellen des Prüfdienstes und Referenzdaten.
-- Läuft nach 01_wave.sh (WAVE-Export) beim ersten Start des Postgres-Containers.

CREATE SCHEMA IF NOT EXISTS ref;
CREATE SCHEMA IF NOT EXISTS app;

-- ArchivPlus-Index: alle seit 01/2025 eingegangenen Rechnungsdokumente (inkl. abgelehnter)
CREATE TABLE IF NOT EXISTS ref.archivplus_index (
    archivplus_id          text PRIMARY KEY,
    eingangsdatum          date,
    kanal                  text,
    dateien                text,
    absender_erkannt       text,
    rechnungsnr_erkannt    text,
    rechnungsdatum         date,
    betrag_brutto_erkannt  numeric(14,2),
    workflow_status        text,
    bearbeiter             text,
    er_nr                  text
);

-- Handelsregister (world/register/index.csv)
CREATE TABLE IF NOT EXISTS ref.register (
    firma            text,
    sitz             text,
    registergericht  text,
    registerart      text,
    registernummer   text,
    status           text,
    datei            text
);
CREATE INDEX IF NOT EXISTS register_firma_idx ON ref.register (lower(firma));

-- Jede Mail, die n8n an den Prüfdienst gibt (auch ohne Rechnung) – Kontext für den Agenten
CREATE TABLE IF NOT EXISTS app.mail_log (
    message_id      text PRIMARY KEY,
    eingang         timestamptz,
    absender        text,
    absender_domain text,
    reply_to        text,
    betreff         text,
    ist_rechnung    boolean,
    anhaenge        jsonb,
    vorgang_id      uuid,
    erfasst_am      timestamptz DEFAULT now()
);

-- Ein Vorgang = eine eingegangene Mail (oder ein Scan) mit Rechnungsdokumenten
CREATE TABLE IF NOT EXISTS app.vorgang (
    id          uuid PRIMARY KEY,
    quelle      text NOT NULL,              -- email | scan | upload
    message_id  text UNIQUE,
    eingang     timestamptz NOT NULL,
    absender    text,
    reply_to    text,
    betreff     text,
    mailtext    text,
    raw_sha256  text,
    srw_job_id  text,
    erstellt_am timestamptz DEFAULT now()
);

-- Unveränderte Dokumente (Ablage auf Volume, hier nur Verweis + Hash)
CREATE TABLE IF NOT EXISTS app.dokument (
    id          uuid PRIMARY KEY,
    vorgang_id  uuid REFERENCES app.vorgang(id),
    dateiname   text,
    typ         text,                       -- pdf | xml
    format      text,                       -- xml-cii | xml-ubl | pdf-text | pdf-scan
    sha256      text NOT NULL,
    pfad        text NOT NULL,
    seiten      int,
    text        text,
    erstellt_am timestamptz DEFAULT now()
);

-- Eine Rechnung (aus einem oder mehreren Dokumenten, z. B. ZUGFeRD = PDF + XML)
CREATE TABLE IF NOT EXISTS app.rechnung (
    id            uuid PRIMARY KEY,
    vorgang_id    uuid REFERENCES app.vorgang(id),
    dokument_ids  uuid[],
    extrakt       jsonb,
    korrekturen   jsonb,                    -- Korrekturen des Agenten an der Extraktion (protokolliert)
    pruefung      jsonb,                    -- letzte Regelprüfung
    erstellt_am   timestamptz DEFAULT now()
);

-- Vorschläge (vom Agenten oder vom Regelwerk = Baseline)
CREATE TABLE IF NOT EXISTS app.vorschlag (
    id            uuid PRIMARY KEY,
    rechnung_id   uuid REFERENCES app.rechnung(id),
    quelle        text NOT NULL,            -- agent | regeln
    entscheidung  text NOT NULL CHECK (entscheidung IN ('freigeben','klaeren','ablehnen')),
    begruendungen jsonb NOT NULL,
    zusammenfassung text,
    freigabe      jsonb,
    kontierung    jsonb,
    skonto        jsonb,
    regelversion  text,
    srw_job_id    text,
    erstellt_am   timestamptz DEFAULT now()
);

-- Entscheidungen der Menschen (Klick in der Mail)
CREATE TABLE IF NOT EXISTS app.entscheidung (
    id            uuid PRIMARY KEY,
    rechnung_id   uuid REFERENCES app.rechnung(id),
    vorschlag_id  uuid REFERENCES app.vorschlag(id),
    aktion        text NOT NULL CHECK (aktion IN ('freigeben','klaeren','ablehnen','vorschlag_falsch')),
    person        text,
    kommentar     text,
    erstellt_am   timestamptz DEFAULT now()
);

-- Prüfprotokoll (GoBD): jede Prüfung mit Eingabe-Hash und Regelversion
CREATE TABLE IF NOT EXISTS app.protokoll (
    id          bigserial PRIMARY KEY,
    zeitpunkt   timestamptz DEFAULT now(),
    rechnung_id uuid,
    ereignis    text,
    akteur      text,
    daten       jsonb
);
