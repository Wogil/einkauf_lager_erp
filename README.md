# Team 2 – Prozess & Transaktion

Projektmodul „Projekt Trost“, Frankfurt UAS, WiSe 2026/27 · Use Case „Angebotserstellung / Einkauf & Lager“

Wir bauen eine gemeinsame, wiederverwendbare Grundlage für transaktionale Geschäftsprozesse: Ein Vorgang kommt
über einen gewohnten Kanal herein (Mail, später Slack/Teams), wird gelesen, gegen Unternehmensdaten und Regeln
geprüft, und ein Mensch bekommt einen begründeten Vorschlag zur Freigabe. Entwickelt und evaluiert wird an den
Szenario-Fällen des Unternehmens Voßkamp Pumpenwerk:

| Fall | Thema | Stand |
|---|---|---|
| **08** | Eingangsrechnungen prüfen und zur Freigabe vorbereiten | ✅ Durchstich von Ende zu Ende (deterministische Baseline) |
| 04 | Angebot aus Kundenanfrage | geplant |
| 11 | Lieferantenangebote vergleichen | geplant |

Grundsätze (siehe [Entscheidungslog](docs/entscheidungslog.md)):

- **Human in the Loop:** Die Lösung schlägt vor, ein Mensch entscheidet. Nichts wird automatisch gebucht, bezahlt
  oder an Stammdaten geändert.
- **Regeln vor Sprachmodell:** Beträge, Freigabegrenzen und Prüfentscheidungen beruhen auf nachvollziehbaren Daten
  und Regeln. Ein LLM leitet keine Werte oder Geschäftsregeln ab.
- **Generisch vs. unternehmensspezifisch:** Ablauf, Prüfmechanik und Agenten sind generisch; Datenquellen,
  Freigabegrenzen, Toleranzen und Kontierung werden pro Unternehmen konfiguriert.

---

## Aktueller Stand auf `main`: Fall 08 als Baseline

Der Ordner [`fall08-stack/`](fall08-stack/) enthält einen lauffähigen Prototyp für Fall 08. Er arbeitet
**rein deterministisch** und ist damit die Baseline (L1), gegen die der agentische Workflow gemessen wird.

```
 Rechnungsmail ──▶ n8n ──▶ Prüfdienst (Regelprüfung) ──▶ Vorschlagsmail ──▶ Sachbearbeitung
                                │                                              │
                     WAVE, Register, Banken                     freigeben / klären / ablehnen
                     ArchivPlus (PostgreSQL)                          (Klick in der Mail)
                                └──────────── Protokoll (GoBD) ◀───────────────┘
```

- Liest XRechnung, ZUGFeRD, PDF mit Text und Scans (OCR)
- Prüft Lieferant, Handelsregister, Bankverbindung, Absender-Domain, Bestellung, Preis, Wareneingang,
  Dubletten, Pflichtangaben, Skonto und Freigabeweg
- Liefert pro Rechnung einen Vorschlag mit Befundcodes und Begründung per Mail; die Entscheidung kommt per
  signiertem Link zurück und wird protokolliert

Details zu Prüfregeln, Architektur und getesteten Fällen: [`fall08-stack/README.md`](fall08-stack/README.md)
· Prozessmodelle (BPMN 2.0): [`fall08-stack/docs/bpmn/`](fall08-stack/docs/bpmn/)

---

## Anleitung: Fall 08 lokal starten

### 1. Voraussetzungen

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (läuft im Hintergrund)
- Python 3 (für das Einspiel-Skript)
- Die **Szenario-Daten** aus dem Kursmaterial (`companies/`, `world/`). Sie liegen **nicht** im Repo.

### 2. Repo klonen und Szenario-Daten ablegen

```bash
git clone https://github.com/Wogil/einkauf_lager_erp.git
cd einkauf_lager_erp
```

Die Ordner `companies/` und `world/` aus dem Kursmaterial direkt in den Repo-Ordner kopieren
(sie sind per `.gitignore` ausgeschlossen):

```
einkauf_lager_erp/
├── companies/        ← Szenario-Daten (nicht im Repo)
├── world/            ← Szenario-Daten (nicht im Repo)
├── docs/
├── fall08-stack/
└── mail-viewer.html
```

### 3. Zugangsdaten anlegen

```bash
cd fall08-stack
cp .env.example .env
```

In der `.env` Passwörter und Tokens setzen (beliebige lange Zufallswerte, z. B. mit `openssl rand -hex 32`).
`PRUEFMODUS=regeln` lassen. **Die `.env` wird nie eingecheckt.**

### 4. Stack starten

```bash
docker compose up -d
```

Der erste Start dauert einige Minuten (Images laden, WAVE-Export einspielen). Danach erreichbar:

| Dienst | Adresse | Wofür |
|---|---|---|
| Mailpit | http://localhost:8025 | Postfach der Sachbearbeitung: hier kommen die Vorschlagsmails an |
| n8n | http://localhost:5678 | Workflow und Ausführungen je Mail |
| Prüfdienst | http://localhost:8000/health | Status und Regelversion |

### 5. Rechnungsmails einspielen

```bash
# alle 96 Mails des Postfachs rechnungseingang@, chronologisch
python3 scripts/replay_eml.py ../companies/a_vosskamp/mail/eml/rechnungseingang@vosskamp-pumpen.example/INBOX
```

Die Vorschläge erscheinen in Mailpit. Mit den Knöpfen in der Mail wird entschieden.

### 6. Erneut testen

Jede Mail wird nur einmal geprüft. Vor einem neuen Durchlauf:

```bash
scripts/reset_testdaten.sh                                      # Prüfergebnisse löschen
docker compose up -d --build --force-recreate pruefdienst n8n   # nur nach Code- oder .env-Änderungen
```

### Mail-Viewer

[`mail-viewer.html`](mail-viewer.html) im Browser öffnen und einen `.eml`-Ordner auswählen, um die Szenario-Mails
übersichtlich zu lesen (läuft komplett lokal).

---

## Evaluation

Wir vergleichen mehrere Varianten auf denselben, fachlich geprüften Testfällen
([Evaluationskonzept](docs/evaluation/evaluationskonzept_fall08.md)):

| Variante | Beschreibung | Status |
|---|---|---|
| B1 | Einfacher Prompt, ohne Tools und Regeln | geplant |
| B2 | Einfaches Skript mit wenigen naheliegenden Prüfungen | geplant |
| **L1** | **Regelprüfung des Prüfdienstes (dieser Stand auf `main`)** | ✅ |
| L2 | Regeln als Leitplanke + Agent (Lesefehler, Zuordnung, Abwägung, Begründung) | nächster Schritt |
| L3 | Regeln + spezialisierte Agenten mit Prüfer | Ausblick |

Gemessen werden Genauigkeit, Konsistenz, Klär- bzw. Eskalationsquote, Kosten und Zeit sowie die Übertragbarkeit
auf andere Unternehmenskontexte.

---

## Nächste Schritte

1. **Branch für den agentischen Workflow (L2):** Agent über die MCP-Tools des Prüfdienstes, Leitplanken bei der
   Validierung des Vorschlags, Vergleich L1 gegen L2
2. **Mandanten-Konfiguration auslagern:** Freigabegrenzen, Toleranzen und Kontierung aus dem Code in eine
   Konfigurationsdatei; Datenzugriff über eine Adapter-Schnittstelle
3. Fälle 04 und 11 auf derselben Grundlage

## Arbeitsweise im Repo

- `main` enthält immer einen lauffähigen Stand.
- Neue Arbeit in eigenen Branches, z. B. `feature/agentic-workflow`, und per Pull Request zurück nach `main`.
- Entscheidungen ins [Entscheidungslog](docs/entscheidungslog.md), Protokolle nach `docs/protokolle/`,
  KI-Nutzung nach [`docs/ki-nutzung.md`](docs/ki-nutzung.md).
- Keine Zugangsdaten und keine Szenario-Daten einchecken.
