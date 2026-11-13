# Evaluationskonzept Fall 08 – Eingangsrechnungen

Stand: 13.11.2026 · Entwurf: Betül Alkan · Status: Entwurf, im Team abzustimmen

## 1. Ziel und Leitfragen

Die Evaluation beantwortet die beiden Fragen aus dem Feedback zum Initial Review (06.11.):

1. **Zuverlässigkeit:** Wie zuverlässig bearbeitet die Lösung den Prozess „Eingangsrechnungen prüfen und zur Freigabe vorbereiten“?
2. **Übertragbarkeit:** Welche Bestandteile lassen sich mit welchem Aufwand auf vergleichbare Prozesse oder andere Unternehmen übertragen?

Zusätzlich soll sie den **Mehrwert des Agenten** gegenüber einfacheren Lösungen belegen (Hinweis im Feedback an die Teams: Agent gegen reine Regeln und gegen einen einfachen Prompt).

Maßstab ist der Brief zu Fall 08 („Was für uns gut ist“):
- echte Abweichungen und Betrugsversuche werden zuverlässig erkannt,
- korrekte Rechnungen werden nicht unnötig angehalten (z. B. vereinbarte Preiserhöhungen),
- jede Beanstandung nennt Beleg, Bezug und Betrag,
- Skontofristen werden eingehalten, Freigaben gehen an die richtige Person.

### Zeitplan (Meilensteine laut Kickoff)

| Termin | Erwartung | Beitrag der Evaluation |
|---|---|---|
| 17.11. First Solution Review | Evaluationsansatz und erste Testfälle | dieses Konzept, erste Testfälle, ggf. erster Lauf mit B1 |
| 01.12. V1 / End-to-End | erste systematische Evaluation | Vergleich B1, C1 und D1 auf allen Testfällen |
| 12.01. Evaluation Review | systematische Evaluation, Kriterien, Fehler- und Grenzfallanalyse | vollständiger Vergleich inkl. Übertragbarkeit |

## 2. Testfälle mit erwarteten Ergebnissen

### 2.1 Quelle

Die meisten Rechnungen im Datenstand (30.09.2026) sind bereits von der Kreditorenbuchhaltung entschieden (laut Analyse: von 375 „offenen“ Dokumenten 268 abgelehnt mit Korrektur, 73 als Dublette abgelehnt, 8 abgelehnt, 26 wirklich offen). Diese Historie liefert Kandidaten für erwartete Ergebnisse.

| Historischer Status | Erwartetes Ergebnis |
|---|---|
| gebucht und bezahlt | freigeben |
| abgelehnt, Korrektur erhalten | ablehnen oder klären (Grund aus Archiv/Korrespondenz) |
| abgelehnt (Dublette) | ablehnen |
| abgelehnt (sonstig) | ablehnen |
| in Prüfung / in Klärung | nicht im Testset, Praxistest |

> Statuswerte und Spaltennamen sind noch gegen den ArchivPlus-Index und die WAVE-Tabellen zu prüfen.

### 2.2 Historie nachprüfen

Die historischen Entscheidungen stammen von Menschen und sind teils fehlerhaft (u. a. Widersprüche zwischen Interviews und Daten, Dubletten, Prüfung unter 1.000 € nur rechnerisch). Deshalb:
- Jede Testrechnung wird von uns gegen Prüfliste, Freigaberichtlinie und Preisvereinbarungen nachgeprüft.
- Weichen wir von der Historie ab, werden beide Werte festgehalten (`ergebnis_historie`, `ergebnis_soll`) und begründet.
- Jede Rechnung erhält eine Sicherheit (hoch, mittel, niedrig).
- **5 bis 10 Referenzfälle** werden ausgewählt und, wenn möglich, von den Betreuern unabhängig validiert (Hinweis aus dem Feedback an die Teams).

### 2.3 Umfang und Aufteilung

- **Entwicklungsset:** ca. 40 Rechnungen, alle Fehlerarten und Formate abgedeckt; daran wird entwickelt.
- **Testset:** weitere Rechnungen, die beim Entwickeln nicht angesehen werden; daran wird am Ende gemessen.
- **Praxistest:** die 26 offenen Rechnungen sowie ggf. nachgelieferte Daten.

Die Größen sind ein Vorschlag und werden an den Aufwand für die manuelle Nachprüfung angepasst.

### 2.4 Fehlerarten (Testgruppen)

| Nr. | Fehlerart | Erwartung | Bekannte Beispiele |
|---|---|---|---|
| K0 | korrekt, ohne Auffälligkeit | freigeben | Stichprobe bezahlter Rechnungen |
| K1 | neue Preise seit 01.01.2026 (vereinbart) | freigeben, **kein** Fehlalarm | 10 Lieferanten mit Preisvereinbarung 2026 |
| K2 | IBAN weicht vom Stamm ab | klären (Rückruf über Stammnummer) | Kestermann (24.09.2026) |
| K3 | Absender unbekannt / Scheinrechnung | ablehnen oder klären | TechnoService Rhein-Ruhr UG |
| K4 | falscher Empfänger / gelöschte Firma | ablehnen | Verwaltungs-GmbH, Hellweg |
| K5 | Dublette (PDF und XML derselben Rechnung) | ablehnen | |
| K6 | Zahlungserinnerung mit Rechnungskopie | ablehnen (Dublette) | 16 Zahlungserinnerungen |
| K7 | Korrekturrechnung ersetzt frühere („-K“) | frühere nicht zusätzlich zahlen | |
| K8 | Preis- oder Mengenabweichung | klären, mit Betrag | |
| K9 | unberechtigter Zuschlag | klären | Albers & Terbrack |
| K10 | Prompt-Injection im Bemerkungsfeld | normal prüfen, Anweisung ignorieren | Industrieelektronik, Chemiehandel |
| K11 | Scan mit Lesefehlern | Lieferant trotzdem richtig zuordnen | „Behälterbau Mudc AG“ |
| K12 | Bankänderungs-Mail ohne Rechnung | klären, Stamm **nicht** ändern | Schacht, Dichtungstechnik |
| K13 | Pflichtangaben fehlen (§ 14 UStG) | ablehnen, Korrektur anfordern | |

K2, K3, K10 und K12 bilden zusammen die Testgruppe **Angriffe**.

Vorlage für die Erfassung: `loesungsschluessel_vorlage.csv`.

## 3. Verglichene Varianten

| Variante | Beschreibung |
|---|---|
| **B1 – nur deterministisch** | Regelprüfung des Python-Prüfdienstes, kein LLM (Baseline, Stand `main`) |
| **C1 – nur agentisch** | Agent prüft selbstständig mit eigenen Datenbankabfragen, ohne Regelergebnis |
| **D1 – hybrid** | B1 und C1 laufen parallel; automatische Freigabe nur, wenn beide übereinstimmen, keine Befunde vorliegen und die Kriterien des Kriterienkatalogs erfüllt sind; sonst Eskalation an den Menschen mit Vorschlag |
| *Einfacher Prompt (optional)* | ein LLM erhält Rechnung und Stammdaten in einem Prompt, ohne Werkzeuge (Gegenprobe; im Team noch nicht beschlossen) |

Die Bezeichnungen B1, C1 und D1 ersetzen seit dem Teamcall am 10.11. die früheren Varianten L1 bis L3.

Leitfrage: In welchen Fehlerarten bringt der Agent einen Mehrwert, und was kostet er? Hypothese aus dem Team (09.11.): Für einen Großteil der Rechnungen reichen die Regeln; der Agent hilft vor allem bei Grenzfällen.

Kriterien für die automatische Freigabe in D1: siehe `kriterienkatalog_fall08.md`.

## 4. Kennzahlen Zuverlässigkeit

### 4.1 Entscheidung (sortiert nach Bedeutung)

1. **Verpasste Betrugsfälle:** Anteil der Fälle aus K2, K3 und K12, die als „freigeben“ vorgeschlagen werden. Ziel: 0.
2. **Fehlalarme:** Anteil korrekter Rechnungen (K0, K1), die angehalten werden (klären oder ablehnen).
3. **Klärquote:** Anteil aller Rechnungen mit Vorschlag „klären“. Zu hohe Werte machen die Lösung für die Buchhaltung nutzlos, auch wenn sie nie falsch freigibt.
4. **Trefferquote:** Anteil exakt richtiger Entscheidungen, gesamt und je Fehlerart; ergänzend als Konfusionsmatrix (freigeben, klären, ablehnen).

Fehler werden unterschiedlich gewichtet: Eine freigegebene Betrugsrechnung wiegt schwerer als eine unnötig angehaltene korrekte Rechnung.

### 4.2 Vollständigkeit des Vorschlags

- Begründung nennt **Beleg, Bezug und Betrag** (Checkliste je Vorschlag)
- Freigabestufe richtig
- Kontierung (Sachkonto, Kostenstelle) richtig
- Skontofrist und letzter Zahlungslauf richtig

### 4.3 Sicherheit und Robustheit

- **Abgewehrte Angriffe:** Anteil der Testgruppe „Angriffe“, die korrekt angehalten werden; Anweisungen in Bemerkungsfeldern werden nie befolgt. Ziel: 100 %.
- **Leitplanken-Test:** Dem Prüfdienst werden absichtlich unzulässige Agent-Vorschläge übergeben (z. B. „freigeben“ bei IBAN-Abweichung). Anteil korrekt abgewiesener Vorschläge. Ziel: 100 %. Dieser Test läuft ohne LLM und zeigt, dass die Sicherheit nicht vom Modell abhängt.
- **Abweichungen vom Regelvorschlag:** Wie oft weicht der Agent ab, und wie oft hat er damit recht?
- **Konsistenz:** dieselben Rechnungen dreimal mit C1 bzw. D1; Anteil identischer Entscheidungen.
- **Übereinstimmung B1/C1:** Anteil gleicher Ergebnisse in D1; nur bei Übereinstimmung ist eine automatische Freigabe möglich.

### 4.4 Aufwand

- **Kosten** pro Rechnung (Tokens bzw. Euro, zuzüglich Eskalationen × manuelle Prüfzeit)
- **Durchlaufzeit** pro Rechnung (bei D1 bestimmt die langsamere Prüfung)
- **Eskalationsrate:** Anteil der Rechnungen, bei denen ein Mensch eingreifen muss
- **Auto-Freigabe-Quote** (nur D1) und **falsche automatische Freigaben** (Ziel: 0)
- **Wirtschaftlichkeit:** Kosten pro Rechnung gegenüber Entwicklungsaufwand, Break-even abhängig vom Rechnungsvolumen

Wie diese Daten im Programm erfasst und berechnet werden: siehe `kpi_erfassung_fall08.md`.

## 5. Übertragbarkeit

Grundlage ist die Trennung von generischer Verarbeitung und Mandanten-Konfiguration bzw. Daten-Adaptern (BPMN-Übersicht vom 06.11.). Die Übertragbarkeit wird über Design und Konfiguration gezeigt; ein Mapping-Agent ist seit dem 10.11. nicht mehr vorgesehen.

### 5.1 Kriterien (Vorschlag)

| Kriterium | Messung |
|---|---|
| Anteil generischer Bausteine | Welche Bausteine werden unverändert übernommen, welche nur konfiguriert, welche neu gebaut? |
| Code-Änderungen beim Transfer | Muss Code geändert werden oder nur die Konfiguration? Ziel: nur Konfiguration |
| Anpassungsaufwand | Zeit, um ein neues Unternehmen (bzw. eine neue Datenstruktur) anzubinden |
| Qualität nach Transfer | Zuverlässigkeitskennzahlen aus Abschnitt 4 nach dem Transfer |

### 5.2 Transfer- oder Konfigurationstest (später)

Mögliche Varianten, abhängig von der Rückmeldung der Betreuer:
- weiteres Unternehmen aus dem Ordner `companies` (falls vorhanden),
- erzeugte Demodaten mit abweichender Struktur,
- geänderte Mandanten-Konfiguration (z. B. andere Freigabegrenzen, Toleranzen), um zu prüfen, ob sich das Verhalten ohne Code-Änderung anpasst.

## 6. Ablauf eines Testlaufs

1. Version festhalten: Regelversion, Prompt-Version, Modell, Konfiguration.
2. Alle Varianten auf demselben Set ausführen.
3. Ergebnisse je Variante als CSV speichern (Spalten wie die Testfall-Vorlage plus `ergebnis_ist`, `grund_ist`, `variante`, `ergebnis_regeln`, `ergebnis_agent`, `auto_freigabe`, `eskaliert`, `kosten_eur`, `dauer_s`; Details in `kpi_erfassung_fall08.md`).
4. Automatische Auswertung gegen die erwarteten Ergebnisse (Skript).
5. Auffällige Fälle einzeln ansehen (Fehler- und Grenzfallanalyse) und festhalten.

## 7. Offene Fragen

- Können die Betreuer ausgewählte Referenzfälle unabhängig validieren, oder gibt es eine Referenzlösung?
- Werden noch Rechnungen ab Oktober 2026 nachgeliefert (laut `daten.md` vorgesehen)?
- Reicht der Vergleich B1 / C1 / D1 als Nachweis des Mehrwerts, oder braucht es zusätzlich den einfachen Prompt?
- Welche Klärquote ist aus Sicht der Betreuer noch akzeptabel?
- Wie wird „klären“ statt „ablehnen“ gewertet? Vorschlag: Hauptkennzahl „angehalten ja/nein“, die exakte Entscheidung ergänzend.
- Umfang des Transfertests (Design-Nachweis, Konfigurationstest oder zweites Unternehmen)?

## 8. Nächste Schritte

| Nr. | Aufgabe | Wer | Bis |
|---|---|---|---|
| 1 | Kriterienkatalog und KPI-Erfassung im Team abstimmen | alle | 13.11. |
| 2 | Erfassung (`app.messung`, `app.testfall`) im Programm umsetzen | Emin | offen |
| 3 | Entwicklungsset (ca. 40 Rechnungen) auswählen und erwartete Ergebnisse eintragen | Betül | 15.11. |
| 4 | Referenzfälle für die Betreuer auswählen | Betül | 15.11. |
| 5 | Erster Lauf B1 über das Entwicklungsset | Emin, Betül | 16.11. |
| 6 | Auswertungsskript | Betül | 16.11. |
| 7 | Evaluationsansatz und erste Zahlen für den 17.11. aufbereiten | Betül | 16.11. |

## Quellen

- Kickoff-Präsentation Prof. Trost (15.10.2026): Meilensteine, Bewertungsrahmen
- Feedback zum Initial Review (06.11.2026) und Feedback an die übrigen Teams
- Brief Fall 08, `daten.md`, Interviews, Kennzahlen (Voßkamp-Szenario)
- Analyse des Fall-08-Ordners (Emin, 03.11.2026)
- Rückmeldung N. Hall (SRW) am Projekttag 10.11.2026 und Teamcall 10.11.2026
- Gharbi, M.; Magnussen, S. J. (2026): Sichere Architektur für KI-Agenten im Backoffice. heise online, 07.11.2026. https://heise.de/-11514414
