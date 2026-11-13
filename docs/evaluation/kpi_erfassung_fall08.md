# Konzept: Erfassung der Kennzahlen (B1, C1, D1)

Stand: 13.11.2026 · Entwurf: Betül Alkan (mit KI-Unterstützung, Claude) · Status: zur Abstimmung im Teamcall 13.11.; Umsetzung im Programm: Emin

## 1. Ziel

Für jede Rechnung und jede Variante werden die Daten erfasst, die für den Vergleich nötig sind:

| Kennzahl | Frage |
|---|---|
| Kosten pro Rechnung | Was kostet eine Prüfung (Modell, Rechenzeit, menschliche Arbeitszeit)? |
| Fehlerrate nach Fehlerart | Wie oft liegt die Variante falsch, getrennt nach Fehlerart (K0 bis K13 im Evaluationskonzept)? |
| Eskalationsrate | Wie oft muss ein Mensch eingreifen? |
| Durchlaufzeit | Wie lange dauert es vom Eingang bis zum Vorschlag bzw. bis zur Entscheidung? |

Daraus folgt die Wirtschaftlichkeitsbetrachtung (Abschnitt 6).

## 2. Was schon erfasst wird

Der Prüfdienst speichert bereits (`db/init/02_app.sql`):
- `app.vorgang`: Eingang, Absender, SRW-Job-ID
- `app.vorschlag`: Quelle (`regeln` oder `agent`), Entscheidung, Begründungen, Freigabe, Kontierung, Skonto, Regelversion
- `app.entscheidung`: Entscheidung des Menschen inkl. „Vorschlag falsch“
- `app.protokoll`: Prüfprotokoll

Es fehlen: Variante und Testlauf, Zeitstempel je Schritt, Modell und Tokens, Ergebnis des Kriterienkatalogs (automatisch freigegeben ja/nein) und der Bezug zum erwarteten Ergebnis.

## 3. Neue Daten je Prüfung

Vorschlag: eine Tabelle `app.messung`, eine Zeile je Rechnung, Variante und Testlauf.

| Feld | Inhalt | Beispiel |
|---|---|---|
| `testlauf_id` | Kennung des Laufs | `2026-11-16_b1_01` |
| `variante` | B1, C1 oder D1 | `D1` |
| `rechnung_id` / `archivplus_id` | Bezug zur Rechnung | `AP-2026-105124` |
| `regelversion`, `prompt_version`, `modell` | Versionsstand | `2026-11-03.2`, `p3`, Modellname |
| `konfiguration` | Schwelle u. a. (aus Kriterienkatalog) | `{"auto_freigabe_schwelle_brutto": 1000}` |
| `format` | xml, pdf-text, pdf-scan | `pdf-scan` |
| `betrag_brutto` | Betrag laut Extraktion | `462.73` |
| `ergebnis_regeln` | B1-Vorschlag | `freigeben` |
| `ergebnis_agent` | C1-Vorschlag (leer bei B1) | `klaeren` |
| `ergebnis_final` | Ergebnis der Variante | `klaeren` |
| `befundcodes` | Liste der Befunde | `["IBAN_ABWEICHUNG"]` |
| `auto_freigabe` | automatisch freigegeben ja/nein (nur D1) | `false` |
| `eskaliert` | ging an einen Menschen | `true` |
| `ausschlussgrund` | erstes erfülltes Ausschlusskriterium (A1–A11) | `A2` |
| `agent_ueberstimmt` | Leitplanke hat Agent-Vorschlag verworfen | `false` |
| `korrekturhinweis_gesendet` | Mail an Lieferanten | `false` |
| `t_eingang`, `t_start`, `t_regeln_fertig`, `t_agent_fertig`, `t_vorschlag` | Zeitstempel | ISO-Zeit |
| `tokens_input`, `tokens_output`, `tool_aufrufe` | Verbrauch des Agenten | `12400`, `850`, `6` |
| `kosten_eur` | berechnet aus Tokens × Preis | `0.04` |
| `fehler` | technischer Fehler oder Zeitlimit | `timeout` |

Zusätzlich aus `app.entscheidung` (nur bei Eskalation): `t_entscheidung`, `aktion_mensch`, `vorschlag_falsch`.

## 4. Erwartete Ergebnisse (Testfälle)

Damit Fehlerraten berechnet werden können, wird die Testfall-Tabelle (`docs/evaluation/loesungsschluessel_vorlage.csv`) als `app.testfall` eingespielt:

| Feld | Inhalt |
|---|---|
| `archivplus_id` | Bezug |
| `kategorie` | Fehlerart K0–K13 |
| `ergebnis_soll` | freigeben, klären, ablehnen |
| `auto_freigabe_soll` | dürfte laut Kriterienkatalog automatisch freigegeben werden |
| `sicherheit` | hoch, mittel, niedrig |

## 5. Berechnung der Kennzahlen

Je Variante und Testlauf:

| Kennzahl | Berechnung |
|---|---|
| Trefferquote | Anteil `ergebnis_final = ergebnis_soll` |
| **Verpasste Betrugsfälle** | Anzahl Fälle der Kategorien K2, K3, K12 mit `ergebnis_final = freigeben` (Ziel 0) |
| **Falsche automatische Freigaben** | Anzahl `auto_freigabe = true` und `ergebnis_soll ≠ freigeben` (Ziel 0) |
| Fehlalarme | Anteil der Fälle mit `ergebnis_soll = freigeben`, die angehalten wurden |
| Fehlerrate nach Fehlerart | Trefferquote je `kategorie` |
| **Eskalationsrate** | Anteil `eskaliert = true` |
| Klärquote | Anteil `ergebnis_final = klaeren` |
| Übereinstimmung B1/C1 | Anteil `ergebnis_regeln = ergebnis_agent` (nur D1) |
| Überstimmungen | Anteil `agent_ueberstimmt = true` |
| Durchlaufzeit System | `t_vorschlag – t_eingang` (Median, 90 %-Wert) |
| Durchlaufzeit gesamt | `t_entscheidung – t_eingang` bei Eskalation, sonst `t_vorschlag – t_eingang` |
| Kosten pro Rechnung | Mittelwert `kosten_eur` (Modell) + Anteil Eskalation × Kosten menschliche Prüfung |
| Konsistenz | gleiche Rechnung dreimal: Anteil identischer `ergebnis_final` (C1, D1) |

Export: je Testlauf eine CSV aus `app.messung` (eine Zeile je Rechnung) und eine Übersicht mit den Kennzahlen je Variante, z. B. per Skript `scripts/kpi_export.py`.

## 6. Wirtschaftlichkeit

Kosten je Rechnung und Variante:

```
Kosten je Rechnung = Modellkosten + Eskalationsrate × Minuten je manueller Prüfung × Kostensatz je Minute
```

Gesamtkosten pro Jahr bei einer Rechnungsmenge N:

```
Kosten pro Jahr = Entwicklungsaufwand (einmalig, anteilig) + N × Kosten je Rechnung
```

Break-even zwischen zwei Varianten X und Y: ab welcher Rechnungsmenge die höheren Entwicklungskosten von X durch geringere laufende Kosten ausgeglichen werden (Hinweis N. Hall, 10.11.).

Annahmen, die wir festlegen und offen benennen müssen:
- Rechnungsmenge Voßkamp: rund 2.300 pro Jahr (Kennzahlen 2025)
- Minuten je manueller Prüfung: Annahme, z. B. aus Durchlaufzeit und Personal abgeleitet (3 Mitarbeitende Kreditoren, eine in Teilzeit)
- Kostensatz je Minute: Annahme
- Modellpreis je 1 Mio. Tokens laut Anbieter zum Zeitpunkt der Messung
- Entwicklungsaufwand je Variante: aus unseren Stunden (grob)

## 7. Umsetzung (Vorschlag)

| Nr. | Schritt | Wer |
|---|---|---|
| 1 | Tabelle `app.messung` und `app.testfall` anlegen, Felder befüllen | Emin |
| 2 | Variante und Testlauf als Parameter beim Start (z. B. `PRUEFMODUS`, `TESTLAUF_ID`) | Emin |
| 3 | Tokens und Tool-Aufrufe aus dem SRW-Job übernehmen | Emin |
| 4 | Testfälle mit erwarteten Ergebnissen erstellen und einspielen | Betül |
| 5 | Export- und Auswertungsskript | Betül (mit Unterstützung) |
| 6 | Annahmen für die Wirtschaftlichkeit festlegen | Betül, im Team abstimmen |

## 8. Offene Fragen

1. Liefert SRW die Tokenzahlen je Job? (Niklas)
2. Wie messen wir die menschliche Prüfzeit (Annahme oder Selbstmessung an einigen Fällen)?
3. Soll die Konsistenz für alle Fälle oder nur eine Stichprobe gemessen werden (Kosten)?
