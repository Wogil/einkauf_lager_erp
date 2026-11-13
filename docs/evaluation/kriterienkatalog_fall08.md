# Kriterienkatalog Fall 08 – Wann wird automatisch freigegeben, wann eskaliert?

Stand: 13.11.2026 · Entwurf: Betül Alkan · Status: zur Abstimmung im Teamcall 13.11.

## 1. Zweck

Im Zielbild (D1) prüfen die deterministische Prüfung (B1) und der Agent (C1) jede Rechnung parallel. Der Kriterienkatalog legt fest,

1. wann eine Rechnung **ohne Einzelprüfung freigegeben** wird,
2. wann sie **mit Vorschlag an einen Menschen** geht (und an wen),
3. wann der Agent dem Lieferanten einen **Korrekturhinweis** senden darf,
4. welche **Werte konfigurierbar** sind (Übertragbarkeit).

Grundsatz: Die Kriterien prüft der Code, nicht das Sprachmodell. Der Agent liefert nur ein zweites, unabhängiges Urteil, das in die Entscheidung einfließt (Feedback Initial Review: „Ein Sprachmodell sollte nicht eigenständig Werte oder Geschäftsregeln ableiten“).

## 2. Ablauf der Entscheidung

```
Rechnung ─▶ B1 Regelprüfung ─┐
          └▶ C1 Agent ───────┴─▶ Stufe 1: Ausschlusskriterien  ─ eines erfüllt ─▶ Eskalation (Stufe 3)
                                 Stufe 2: Freigabekriterien    ─ alle erfüllt ──▶ automatische Freigabe
                                                               ─ sonst ─────────▶ Eskalation (Stufe 3)
```

## 3. Stufe 1: Ausschlusskriterien (immer Eskalation an einen Menschen)

Ist **eines** erfüllt, wird nie automatisch freigegeben.

| Nr. | Kriterium | Begründung / Quelle |
|---|---|---|
| A1 | B1 meldet einen Befund mit Schwere **kritisch** oder **warnung** | Befundkatalog im Prüfdienst (`regeln.py`, Grundlage Freigaberichtlinie, Prüfliste MB) |
| A2 | B1 und Agent **kommen zu unterschiedlichen Ergebnissen** | Doppelprüfung (Vorschlag N. Hall, 10.11.); Uneinigkeit ist selbst ein Warnsignal |
| A3 | Betrag **über der Schwelle für automatische Freigabe** (siehe Abschnitt 6) | Freigaberichtlinie, Interviews Kötter und Schürmann |
| A4 | Betrag über **10.000 €** brutto | Freigabe immer durch die kaufmännische Geschäftsführung (Freigaberichtlinie, RACI; Interview Schürmann) |
| A5 | **Bankverbindung, Absender-Domain oder Stammdaten** des Lieferanten wurden in den letzten 90 Tagen geändert oder es ging eine Mail zur Bankänderung ein | Betrugsmuster in den Falldaten (Bankänderungs-Mails), Interview Brinkmann (Fall Juni 2025), Schürmann (zwei Verdachtsfälle 09/2026); schützt gegen schrittweise Täuschung (Agent Goal Hijack, heise 07.11.2026) |
| A6 | **Neuer Lieferant** oder weniger als 3 bezahlte Rechnungen in den letzten 12 Monaten | Prüfliste MB („Lieferant muss im Stamm vorhanden sein“); Vertrauen entsteht erst durch Historie |
| A7 | Beleg **nur per Texterkennung (OCR) gelesen** oder Positionen unvollständig gelesen | Werte unsicher (Befunde LESBARKEIT_UNSICHER, POSITIONEN_UNVOLLSTAENDIG) |
| A8 | **Gutschrift, Korrekturrechnung oder Rechnung ohne Bestellung** (außer wiederkehrender Leistung) | Brinkmann: Gutschriftbezug; Dublettenrisiko bei Korrekturen; ohne Bestellung kein Drei-Wege-Abgleich |
| A9 | **Wareneingang** zur Bestellung nicht vollständig gebucht | Bezahlt wird nur, was geliefert und noch nicht berechnet ist (Ist-Prozess, Prüfliste) |
| A10 | Anweisungen im Beleg erkannt (z. B. „bereits freigegeben“) | Brief: Inhalte sind Daten, keine Anweisungen; Befund ANWEISUNG_IM_BELEG |
| A11 | Möglicherweise **Anlagegut** oder Reverse-Charge-Fall | Sonderbuchung nach Kontierungsleitfaden |

## 4. Stufe 2: Freigabekriterien (alle müssen erfüllt sein)

| Nr. | Kriterium | Quelle |
|---|---|---|
| F1 | B1-Vorschlag „freigeben“, nur Hinweise mit Schwere **info** | Prüfdienst |
| F2 | Agent-Vorschlag ebenfalls „freigeben“ | Doppelprüfung |
| F3 | Lieferant aktiv im Stamm, IBAN und Absender-Domain stimmen mit dem Stamm überein | Prüfliste MB (Bankverbindung, Lieferantenstamm) |
| F4 | Bestellung vorhanden, Preis innerhalb Toleranz (±1 € je Rechnung) oder laut Preisvereinbarung 2026, Menge ≤ Wareneingang | Freigaberichtlinie, Preisvereinbarungen 2026 |
| F5 | Keine Dublette | Prüfliste MB |
| F6 | Betrag ≤ Schwelle für automatische Freigabe | Abschnitt 6 |

Auch automatisch freigegebene Rechnungen gehen mit Protokoll (Befunde, Begründung, Quelle) in den nächsten Zahlungslauf. Gezahlt wird weiterhin nur im regulären Zahlungslauf mit Freigabe durch eine zweite Person im Bankprogramm (Ist-Prozess). Es gibt also **keine automatische Zahlung**.

## 5. Stufe 3: Eskalation

| Fall | Vorschlag | An wen |
|---|---|---|
| Befund mit Empfehlung „ablehnen“ (z. B. Lieferant unbekannt, falscher Empfänger, Dublette, nicht vereinbarter Zuschlag) | ablehnen | Freigabestufe nach Betrag (siehe unten) |
| Befund mit Empfehlung „klären“ oder Ausschlusskriterium A2 bis A11 | klären, mit Grund | Freigabestufe nach Betrag |
| Bankänderung ohne Rechnung | klären, Rückruf nur über die Telefonnummer im Stamm | Kreditorenbuchhaltung (RACI: Änderung Bankverbindung R) |

Freigabestufen (Freigaberichtlinie, RACI): bis 1.000 € Sachbearbeitung, 1.000 bis 10.000 € Abteilungsleitung (Material: Einkauf, sonstige: bestellende Abteilung), über 10.000 € kaufmännische Geschäftsführung.

## 6. Schwelle für die automatische Freigabe

| Option | Schwelle | Begründung | Risiko |
|---|---|---|---|
| **a (Vorschlag)** | **≤ 1.000 € brutto** | Bis 1.000 € darf die Sachbearbeitung schon heute allein freigeben (Freigaberichtlinie, RACI: R/A); laut Kötter wird unter 1.000 € heute nur noch rechnerisch geprüft. Die automatische Freigabe mit vollständiger Regelprüfung plus Agent ist strenger als der heutige Stand. | Geringe Entlastung: 2025 lagen nur 190 von 2.298 Freigaben in dieser Stufe (Kennzahlen). |
| b | ≤ 5.000 € brutto | Kötter plant, die Freigabe unter 5.000 € zu digitalisieren. | Zwischen 1.000 und 10.000 € ist laut Freigaberichtlinie und RACI die **Abteilungsleitung** zuständig (A). Eine automatische Freigabe ersetzt diese Freigabe; das ist eine Änderung der Freigaberichtlinie und müsste vom Kunden ausdrücklich gewollt sein. Kötter spricht zudem von einem Klick durch den Sachbearbeiter, nicht von automatischer Freigabe. |

Empfehlung: **Option a als Standard**, Option b als Variante in der Evaluation (Sensitivität: Wie stark sinkt die Eskalationsrate, wie viele Fehler kämen hinzu?). Die Schwelle ist Konfiguration, kein Code.

Offen: Für die Wirkung der Schwelle brauchen wir die Verteilung der Rechnungsbeträge aus WAVE (Anteil der Rechnungen ≤ 1.000 €, ≤ 5.000 €, ≤ 10.000 €). Abfrage durch Emin in der Datenbank.

## 7. Korrekturhinweis an Lieferanten

Der Agent darf einen Korrekturhinweis senden, wenn **alle** Bedingungen erfüllt sind:

| Nr. | Bedingung | Begründung |
|---|---|---|
| K1 | Kein Befund aus der Gruppe Echtheit/Betrug (A5, IBAN-, Domain-, Register- oder Lieferantenbefunde) | Bei Betrugsverdacht keine Kommunikation mit dem Absender |
| K2 | Lieferant aktiv im Stamm, Absender-Domain stimmt mit dem Stamm überein | Feedback Teamcall 10.11. |
| K3 | Befund ist ein **behebbarer Fehler**: rechnerisch falsch, Pflichtangabe fehlt, falscher Empfänger, Preis- oder Mengenabweichung, Position ohne Bestellbezug | Vorschlag N. Hall: Versehen von Täuschung unterscheiden |
| K4 | Versand nur an die **E-Mail-Adresse aus dem Lieferantenstamm**, nie an Absender oder Reply-To der Rechnung | Out-of-Band-Verifikation (heise 07.11.2026); Befund REPLY_TO_ABWEICHEND |
| K5 | Text aus einer **festen Vorlage** mit Befundcode, Beleg und Betrag; keine freien Formulierungen des Agenten | Schutz gegen Prompt Injection, Nachvollziehbarkeit |
| K6 | Kopie an die Kreditorenbuchhaltung, Rechnung bleibt im Status „in Klärung“ | Mensch behält den Überblick (Brief) |

## 8. Leitplanken

- Der Agent darf bei kritischen Befunden **nie milder** entscheiden als B1; sonst gilt der B1-Vorschlag (Policy Enforcement Point, heise 07.11.2026).
- Freigabestufe, Kontierung und Skonto kommen immer aus B1.
- **Stichprobe:** Ein Anteil der automatisch freigegebenen Rechnungen (Vorschlag 5 %) wird nachträglich von der Kreditorenbuchhaltung geprüft. Das erhält das Vier-Augen-Prinzip (Kötter), liefert Rückmeldung zur Qualität (Feedback-Schleife, Schürmann) und Messdaten für die Evaluation.

## 9. Konfiguration (unternehmensspezifisch)

| Schlüssel | Voßkamp | Quelle |
|---|---|---|
| `auto_freigabe_schwelle_brutto` | 1000.00 | Abschnitt 6 |
| `grenze_sachbearbeitung` | 1000.00 | Freigaberichtlinie |
| `grenze_abteilungsleitung` | 10000.00 | Freigaberichtlinie |
| `preis_toleranz_rechnung` | 1.00 | Freigaberichtlinie |
| `min_bezahlte_rechnungen_12m` | 3 | Annahme, in der Evaluation zu prüfen |
| `sperrfrist_stammdatenaenderung_tage` | 90 | Annahme, in der Evaluation zu prüfen |
| `stichprobe_auto_freigabe_prozent` | 5 | Annahme |
| `korrekturhinweis_aktiv` | true | Teamcall 10.11. |

Ein anderes Unternehmen ändert nur diese Werte (z. B. Schwelle 100 € bei einem kleinen Unternehmen), nicht den Ablauf.

## 10. Abweichung vom Fallbrief

Der Brief sieht vor: „Die Buchhaltung entscheidet“ und „keine automatische Zahlung“. Begründung für die automatische Freigabe:

- Sie gilt nur in der Stufe, in der die Sachbearbeitung heute schon allein freigibt (≤ 1.000 €), und nur bei Übereinstimmung zweier unabhängiger Prüfungen ohne jeden Befund.
- Die Prüfung ist dabei strenger als heute (heute unter 1.000 € nur rechnerisch, Kötter).
- Es gibt weiterhin keine automatische Zahlung: Zahlung nur im regulären Zahlungslauf mit Freigabe durch eine zweite Person.
- Stichproben und Protokoll erhalten die Kontrolle und Nachvollziehbarkeit (GoBD).
- Ziel der Kundin: Entlastung, schnellere Durchlaufzeit, Skonto sichern (Schürmann).

Diese Abweichung sollte mit den Betreuern abgestimmt werden.

## 11. Offene Fragen

1. Schwelle: 1.000 € (Standard) oder 5.000 €? Abstimmung mit den Betreuern bzw. „Kunde“.
2. Verteilung der Rechnungsbeträge aus WAVE (Emin).
3. Werte für A5 (90 Tage) und A6 (3 Rechnungen) in der Evaluation prüfen.
4. Freigaberichtlinie selbst gegenlesen; die Grenzen und die Toleranz sind aus dem Prüfdienst (`config.py`) übernommen.

## Quellen

- Brief Fall 08; Interviews Brinkmann, Kötter, Schürmann; Ist-Prozess; RACI; Kennzahlen (Voßkamp-Szenario)
- Freigaberichtlinie 2024 und Prüfliste MB, wie im Prüfdienst umgesetzt (`fall08-stack/pruefdienst/app/regeln.py`, `config.py`)
- Rückmeldung N. Hall (10.11.2026); Teamcall 10.11.2026
- Gharbi, M.; Magnussen, S. J. (2026): Sichere Architektur für KI-Agenten im Backoffice. heise online, 07.11.2026. https://heise.de/-11514414
