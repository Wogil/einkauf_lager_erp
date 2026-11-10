# Fall 08 – Eingangsrechnungen prüfen (Voßkamp)

Prototyp für den Projektfall 08: Eine Rechnung kommt per Mail an, wird gelesen, gegen WAVE,
Lieferantenstamm, Handelsregister und Richtlinien geprüft, und die zuständige Person bekommt einen
begründeten Vorschlag **freigeben / klären / ablehnen** per Mail. Die Person entscheidet per Klick.
Nichts wird automatisch gebucht oder bezahlt.

```
 .eml / IMAP ──▶ n8n ──────────────▶ Prüfdienst (REST)          SRW (Hochschule)
                  │  1. Mail einliefern   │ legt Vorgang an,          │
                  │  2. Rechnung? sonst   │ liest PDF/XML/Scan        │
                  │     nur protokolliert │                            │
                  │  3a. Modus regeln ────▶ Regelprüfung (Baseline)    │
                  │  3b. Modus srw ─── Job starten ──────────────────▶ Expert „Rechnungsprüfer“
                  │                       │◀──── MCP-Tools ─────────── │ prüft, schlägt nach,
                  │                       │                            │ speichert Vorschlag
                  │  4. Vorschlag-Mail ──▶ Mailpit (Postfach der Mitarbeitenden)
                  │  5. Klick in der Mail ▶ Entscheidung speichern (+ SRW-Job abschließen)
                  └───────────────────────────────────────────────────────────────────
 PostgreSQL: WAVE-Export (Schema wave), Register + ArchivPlus-Index (ref), Prüfdienst (app), n8n
```

## Bestandteile

| Ordner | Inhalt |
|---|---|
| `docker-compose.yml` | Stack: PostgreSQL, Prüfdienst, n8n, Mailpit |
| `db/init/` | Lädt beim ersten Start den WAVE-Export **mit dem Original-Skript des Kunden**, Register- und ArchivPlus-Index, legt die Tabellen des Prüfdienstes an |
| `pruefdienst/` | Python (FastAPI): Mail/PDF/XRechnung/ZUGFeRD/Scan lesen, Prüfregeln, MCP-Server für SRW, Ergebnis-Mail |
| `n8n/workflows/` | Workflow „Rechnungseingang“ und „Entscheidung aus Mail“ (werden beim Start importiert) |
| `srw/` | Expert-Konfiguration „Rechnungsprüfer“ und Connector-Definition für den Prüfdienst |
| `scripts/replay_eml.py` | Spielt `.eml`-Dateien so ein, als kämen sie gerade an |

Der Stack erwartet, dass er **im Szenario-Ordner** liegt (neben `companies/` und `world/`).
Die Daten werden nur lesend eingebunden.

## Starten

```bash
cp .env.example .env          # Passwörter/Token setzen
docker compose up -d --build  # erster Start dauert ~1–2 Min. (WAVE-Daten werden geladen)
```

| Was | Adresse |
|---|---|
| n8n (Workflows, Ausführungen) | http://localhost:5678 – beim ersten Aufruf Konto anlegen |
| Mailpit (so sehen Frau Brinkmann & Co. die Vorschläge) | http://localhost:8025 |
| Prüfdienst (API-Doku) | http://localhost:8000/docs |

Mails einspielen:

```bash
# alle 96 Mails der INBOX (Stand 30.09.2026), chronologisch
python3 scripts/replay_eml.py ../companies/a_vosskamp/mail/eml/rechnungseingang@vosskamp-pumpen.example/INBOX

# einzelne Demo-Fälle
python3 scripts/replay_eml.py ../companies/a_vosskamp/mail/eml/rechnungseingang@vosskamp-pumpen.example/INBOX/2026-09-24_A-ER-003679.eml
```

Danach in Mailpit die Vorschläge ansehen und auf *Freigeben / Klären / Ablehnen* klicken.

**Erneut testen:** Jede Mail wird nur einmal geprüft (gleiche Message-ID). Wer dieselben Mails noch einmal einspielt,
sieht sie in n8n im Zweig „Bereits verarbeitet – übersprungen“. Vorher zurücksetzen:

```bash
scripts/reset_testdaten.sh        # löscht nur die Prüfdienst-Daten, WAVE und n8n bleiben
```

**Nach einem Update** der Workflows oder des Prüfdienstes:

```bash
docker compose up -d --build --force-recreate pruefdienst n8n
```

In n8n kurz prüfen, ob der Workflow „Fall 08 – Rechnungseingang“ den neuen Stand zeigt.

## Prüfmodus

`PRUEFMODUS` in `.env`:

- **`regeln`** – nur die festen Regeln (ohne Sprachmodell). Läuft sofort, ist die **Skript-Baseline** für die Evaluation.
- **`srw`** – n8n startet pro Vorgang einen SRW-Job. Der Agent nutzt die MCP-Tools, bewertet die Befunde,
  löst Unklarheiten (z. B. Scans) und speichert den Vorschlag. Speichert der Agent nichts (Fehler, Timeout),
  greift automatisch die Regelprüfung als Rückfallebene – die Buchhaltung bekommt in jedem Fall eine Mail.

### SRW einrichten (einmalig)

1. **Prüfdienst von außen erreichbar machen** (SRW läuft bei der Hochschule): Port 8000 hinter HTTPS
   (z. B. Caddy/nginx auf dem Server) – `PRUEFDIENST_PUBLIC_URL` setzen.
2. **Connector anlegen**: `srw/connector-pruefdienst.json` ausfüllen und an `POST {SRW}/api/datasources` schicken
   (oder im Cockpit: Connectors → MCP-Server, Transport `http`, Bearer-Token = `PRUEFDIENST_TOKEN`).
3. **Expert importieren**: `srw/expert/rechnungspruefer.yaml` (Cockpit → Experts → Import).
4. **Projekt** anlegen, Connector und Expert zuordnen, `SRW_PROJECT_ID` und `SRW_EXPERT` in `.env` setzen.
5. **API-Key** (`ak_…`) mit den Rechten `jobs:read` und `jobs:write` in `.env` als `SRW_API_KEY`.
6. `PRUEFMODUS=srw`, dann `docker compose up -d`.

Test der Verbindung: `curl -H "Authorization: Bearer $SRW_API_KEY" $SRW_API_URL/api/experts`

## MCP-Tools für den Agenten

| Tool | Zweck |
|---|---|
| `lese_vorgang` | Mail-Kopf, Mailtext (als nicht vertrauenswürdig markiert), erkannte Rechnungen |
| `lese_rechnung` | Extrahierte Daten, optional Volltext |
| `pruefe_rechnung` | **Alle festen Regeln** → Befunde, Kontierung, Freigabestufe, Skonto, Regelvorschlag. Mit `korrekturen` lassen sich falsch gelesene Felder berichtigen (protokolliert) |
| `seitenbild` | PDF-Seite als Bild (Scans) |
| `get_lieferant`, `get_bestellung`, `suche_rechnungen`, `get_preisvereinbarung`, `suche_register`, `get_mailverlauf` | Nachschlagen in WAVE, ArchivPlus, Register, Mail-Protokoll |
| `speichere_vorschlag` | Vorschlag mit Begründungen (Beleg, Bezug, Betrag). Kontierung, Freigabe und Skonto übernimmt der Prüfdienst – der Agent kann sie nicht verändern |

## Prüfregeln

Alle Regeln stehen an einer Stelle: `pruefdienst/app/regeln.py` (zum Justieren gegen die Evaluation).
Die Regelprüfung arbeitet **zum Stichtag des Eingangs**: Spätere Buchungen zählen nicht – so lassen sich auch
historische Mails korrekt prüfen.

| Code | Schwere | Empfehlung | Bedeutung |
|---|---|---|---|
| `LIEFERANT_UNBEKANNT` | kritisch | ablehnen | Rechnungssteller weder im Lieferantenstamm noch im Handelsregister |
| `LIEFERANT_NEU` | warnung | klären | Rechnungssteller nicht im Lieferantenstamm (Einkauf fragen) |
| `LIEFERANT_GELOESCHT` | kritisch | ablehnen | Rechnungssteller im Handelsregister gelöscht |
| `IBAN_ABWEICHUNG` | kritisch | klären | Bankverbindung weicht vom Lieferantenstamm ab |
| `IBAN_UNGUELTIG` | kritisch | klären | IBAN-Prüfziffer ungültig |
| `IBAN_ANDERER_LIEFERANT` | kritisch | klären | IBAN gehört laut Stamm zu einem anderen Lieferanten |
| `BANK_BLZ_WIDERSPRUCH` | warnung | klären | Bankname/BIC passt nicht zur Bankleitzahl der IBAN |
| `ABSENDER_DOMAIN_IMITAT` | kritisch | klären | Absender-Domain imitiert die Domain des Lieferanten |
| `ABSENDER_DOMAIN_FREMD` | warnung | klären | Absender-Domain gehört nicht zum Lieferanten |
| `REPLY_TO_ABWEICHEND` | warnung | klären | Antwortadresse (Reply-To) weicht vom Absender ab |
| `BANKAENDERUNG_MAIL_VORHER` | warnung | klären | Vorher ging eine Mail zur Bankänderung von ähnlicher Domain ein |
| `BANKAENDERUNG_MAIL_HINWEIS` | info | freigeben | Frühere Bankänderungs-Mail bekannt, diese Rechnung nutzt aber die Stamm-IBAN |
| `REGISTER_ABWEICHUNG` | warnung | klären | Registerangabe auf der Rechnung passt nicht zum Handelsregister |
| `REGISTERANGABE_FEHLT` | warnung | klären | Keine Registerangabe trotz eintragungspflichtiger Rechtsform |
| `ANWEISUNG_IM_BELEG` | warnung | klären | Bemerkungsfeld enthält Anweisungen an automatisierte Systeme (ignoriert) |
| `PDF_XML_WIDERSPRUCH` | kritisch | klären | PDF und XML der Rechnung widersprechen sich |
| `FALSCHER_EMPFAENGER` | kritisch | ablehnen | Rechnung an falsche Gesellschaft adressiert (§ 14 UStG) |
| `PFLICHTANGABE_FEHLT` | kritisch | ablehnen | Pflichtangabe nach § 14 UStG fehlt |
| `RECHNERISCH_FALSCH` | kritisch | ablehnen | Rechnung rechnerisch falsch |
| `REVERSE_CHARGE_HINWEIS_FEHLT` | warnung | klären | Auslandslieferant ohne Hinweis auf Steuerschuldnerschaft |
| `DUBLETTE` | kritisch | ablehnen | Rechnung liegt bereits vor (gleicher Lieferant, gleiche Rechnungsnummer) |
| `MOEGLICHE_DUBLETTE` | warnung | klären | Gleicher Betrag kurz zuvor bereits berechnet |
| `KORREKTUR_ORIGINAL_BEZAHLT` | kritisch | klären | Korrekturrechnung, Original wurde bereits bezahlt |
| `BESTELLUNG_FEHLT` | warnung | klären | Keine Bestellnummer (Rückfrage beim Besteller) |
| `BESTELLUNG_UNBEKANNT` | warnung | klären | Bestellnummer in WAVE nicht gefunden |
| `BESTELLUNG_ANDERER_LIEFERANT` | kritisch | klären | Bestellung gehört zu einem anderen Lieferanten |
| `PREIS_ABWEICHUNG` | warnung | klären | Preis über Bestellung bzw. Preisvereinbarung |
| `MENGE_UEBER_WARENEINGANG` | warnung | klären | Berechnete Menge größer als geliefert und noch nicht berechnet |
| `WARENEINGANG_FEHLT` | warnung | klären | Zur Bestellung ist noch kein Wareneingang gebucht |
| `ZUSCHLAG_NICHT_VEREINBART` | kritisch | ablehnen | Nicht vereinbarter Zuschlag berechnet |
| `POSITION_OHNE_BESTELLBEZUG` | warnung | klären | Rechnungsposition ohne passende Bestellposition |
| `GUTSCHRIFT_OHNE_BEZUG` | warnung | klären | Gutschrift ohne erkennbaren Bezug auf eine Rechnung |
| `POSITIONEN_UNVOLLSTAENDIG` | warnung | klären | Positionen nicht vollständig gelesen (Summe ≠ Netto) – am Beleg prüfen |
| `LESBARKEIT_UNSICHER` | warnung | klären | Dokument nur per Texterkennung gelesen, Werte unsicher |
| `PREISVEREINBARUNG_ANGEWENDET` | info | freigeben | Preis entspricht der Preisvereinbarung 2026 (höher als Bestellpreis) |
| `PREIS_UNTER_REFERENZ` | info | freigeben | Preis unter Bestellung/Preisvereinbarung |
| `WIEDERKEHRENDE_LEISTUNG` | info | freigeben | Wiederkehrende Leistung ohne Bestellung (üblich bei diesem Lieferanten) |
| `KORREKTUR_ERSETZT` | info | freigeben | Korrekturrechnung ersetzt eine frühere Rechnung |
| `ZAHLUNGSBEDINGUNG_ABWEICHEND` | info | freigeben | Zahlungsbedingung auf der Rechnung weicht vom Stamm ab |
| `DUPLIKAT_VERMERK` | info | freigeben | Dokument trägt Vermerk Duplikat/Kopie |
| `SKONTO_FRIST_KNAPP` | info | freigeben | Skontofrist läuft bald ab |
| `ANLAGEGUT_HINWEIS` | info | freigeben | Möglicherweise Anlagegut (> 800 € netto) – Anlagenbuchhaltung informieren |

Grundlagen: Freigaberichtlinie (2024), Prüfliste MB (14 Punkte), Kontierungsleitfaden SKR04, Preisvereinbarungen 2026, Brief Fall 08.

## Sicherheit und Nachvollziehbarkeit

- **Nur lesender Zugriff auf WAVE.** Keine Zahlung, keine Stammdatenänderung – technisch, nicht nur per Prompt.
- **Inhalte sind Daten:** Mailtexte und Bemerkungsfelder werden nie als Anweisung ausgeführt. Anweisungen an
  „automatisierte Systeme“ in Belegen werden als Befund `ANWEISUNG_IM_BELEG` gemeldet.
- **GoBD:** Originale (Mail + Anhänge) werden unverändert mit SHA-256 abgelegt (`app.dokument`), jede Prüfung,
  jeder Vorschlag und jede Entscheidung steht mit Zeitpunkt und Regelversion in `app.protokoll`.
- **Signierte Links** in den Mails (HMAC) – ein Link gilt nur für genau eine Rechnung und Aktion.
- Datenbank ohne Port nach außen; Prüfdienst und MCP nur mit Token.

## Beim Kunden (Übertragbarkeit)

Nur die `.env` ändert sich: WAVE-Lesezugriff statt CSV-Kopie, IMAP der Groupware statt `.eml`,
SMTP/Teams statt Mailpit, eigene SRW-Instanz. Prüfregeln, Workflows und Expert bleiben gleich.

## Getestete Fälle (Regelmodus, echte Szenario-Mails)

| Mail | Ergebnis | Befunde |
|---|---|---|
| Käster 25050495 – „Zahlungserinnerung“ mit Rechnungskopie | **ablehnen** | Dublette von ER25-10976 (bereits bezahlt) |
| Blechbearbeitung Stey 90002499 | **ablehnen** | an „Voßkamp Verwaltungs-GmbH“ adressiert |
| Sorgatz R25-0647 (zweite Zusendung, „Duplikat“) | **ablehnen** | Dublette – genau die 48.259,32 €, die 2025 doppelt bezahlt wurden |
| Albers AT-2025-00466 | **ablehnen** | „Zuschlag Express-Sonderfahrt“ 1.350,46 € nicht vereinbart |
| Albers AT-2025-00466/1 (Korrektur) | freigeben | ersetzt abgelehnte Rechnung |
| Dehmel R26-0400 | **klären** | 15-kW-Motor 1.011,05 € statt 972,16 € lt. Preisvereinbarung (+350,01 €) |
| Schacht 90004676 | **klären** | 4 Motoren berechnet, nur 3 geliefert und noch nicht berechnet – Lieferant schickte später genau diese Korrektur |
| Jacobi RG-000726-N | **klären** | Prompt-Injection im XML („Note to AI assistant …“) + Preis über Bestellung (+241,50 €) |
| Albers AT-2026-00570 | **klären** | Preis Pos. 14 über Preisvereinbarung; die spätere Korrektur …570K wird freigegeben |
| Kestermann RE 26/0516 | **ablehnen** | IBAN ≠ Stamm, Absender-Domain mit einem „n“ zu wenig, Bankänderungs-Mail zwei Tage vorher, Rechnung bereits gebucht |
| TechnoService Rhein-Ruhr UG 2026-672 | **ablehnen** | weder im Lieferantenstamm noch im Handelsregister, keine Registerangabe, keine Bestellung |
| Junk Leiterplattenfertigung 202600395 | **ablehnen** | weder USt-IdNr. noch Steuernummer (§ 14 UStG) |
| Heser, Wernecke, Speer, Jäkel, Albers AT-2026-00571 | freigeben | ohne Beanstandung; Freigabe an die richtige Person (Brinkmann ≤ 1.000 €, Schnittker ≤ 10.000 €, Dr. Schürmann darüber; vor 03/2026 Böckenhoff) |

Zusätzlich Ende-zu-Ende in n8n 2.46 getestet: Webhook → Prüfdienst → Vorschlags-Mail → Klick (Freigeben/Klären/Ablehnen,
„Vorschlag war falsch“ mit Kommentar, manipulierter Link wird abgewiesen). Der SRW-Modus wurde mit einer Attrappe der
SRW-API getestet, die die MCP-Tools wie ein Agent aufruft (Job starten, Status abfragen, Vorschlag speichern, Job freigeben) –
der Test mit dem echten SRW-Agenten steht noch aus.

### Parser-Massentest (alle Belege 01/2025–09/2026, 5.109 Dokumente mit Text/XML)

`python3 tests/parser_massentest.py ../companies/a_vosskamp/archivplus/Eingangsrechnungen/2025 ../companies/a_vosskamp/archivplus/Eingangsrechnungen/2026`

| Format | Anzahl | Rechnungsnr. | Brutto | IBAN | USt-Id/StNr | Positionen | Summe = Netto |
|---|---|---|---|---|---|---|---|
| ZUGFeRD (CII) | 1.275 | 100 % | 100 % | 100 % | 100 % | 100 % | 100 % |
| XRechnung (UBL) | 595 | 100 % | 100 % | 99 % | 100 % | 100 % | 99 % |
| PDF mit Text | 3.239 | 100 % | 100 % | 100 % | 100 % | 100 % | 100 % |

Umbrochene Beträge in schmalen Tabellenspalten (z. B. Dehmel, Zeitarbeit Klemm, Meyer, Heinz: `22.359,6` + Folgezeile `8`)
werden wieder zusammengesetzt. Weicht die Positionssumme bei einem PDF trotzdem ab, meldet die Prüfung
`POSITIONEN_UNVOLLSTAENDIG` (klären, am Beleg nachlesen) statt „rechnerisch falsch“ – ein Lesefehler darf nie zur Ablehnung führen.

Bestellnummern werden in 92 % gefunden – der Rest sind Dienstleistungen ohne Bestellung (Energie, Leasing, Software),
die als „wiederkehrende Leistung“ erkannt werden. 87 Scans laufen über Texterkennung (Tesseract, Deutsch) und werden
zusätzlich als „Lesbarkeit unsicher“ markiert.

## Bekannte Grenzen

- PDF-Positionen werden per Layout-Erkennung gelesen; bei ungewöhnlichen Layouts fehlen sie → der Agent liest
  per `lese_rechnung(mit_volltext)`/`seitenbild` nach und korrigiert.
- Die Freigabe zwischen 1.000 und 10.000 € außerhalb von Material wird über die Kostenstelle abgeleitet
  (Abteilungsleitung) – mit dem Kunden zu bestätigen.
- Ob unter 1.000 € nur rechnerisch geprüft wird (Aussage Frau Kötter) oder voll (Richtlinie), ist offen;
  der Prototyp prüft voll.
