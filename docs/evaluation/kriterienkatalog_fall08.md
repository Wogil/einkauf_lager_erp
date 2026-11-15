# Kriterienkatalog Fall 08 – Welcher Weg für welche Rechnung?

Stand: 13.11.2026 · Entwurf: Betül Alkan · Status: zur Abstimmung im Teamcall 15.11.; Grundlage für die Testfälle (Nicolas, A-36) · Issue: #43

## 1. Zweck und Grundsätze

Der Katalog legt fest, über welchen Weg eine Rechnung läuft und an wen der Vorschlag geht. Er gilt für den mehrstufigen Ansatz, den Nicolas und Betül am 13.11. vorgeschlagen haben. Die Abstimmung mit Emin steht aus (A-38).

1. Die **deterministische Prüfung (B1)** prüft jede Rechnung.
2. Der **Agent** prüft nur, wenn B1 einen klärbaren Prüfbedarf meldet.
3. **Ein Mensch entscheidet immer.** Standardfälle gibt er mit einem Klick frei.

Grundsätze:
- **Keine automatische Freigabe und keine automatische Zahlung.** Laut Brief entscheidet die Buchhaltung. Frau Dr. Schürmann sieht rund 90 % der Rechnungen als Standardfälle, „aber das heißt nicht, dass wir sie einfach durchwinken dürfen“. Frau Kötter plant, dass das System prüft und kontiert und die Sachbearbeitung nur noch „Genehmigen“ oder „Ablehnen“ klickt.
- **Die Kriterien prüft der Code, nicht das Sprachmodell.** Das Sprachmodell soll keine Werte oder Geschäftsregeln selbst ableiten (Feedback Initial Review).
- **Ausschlusskriterien gehen vor.** Ein kritischer Befund führt immer direkt zur Eskalation, unabhängig von einem Score oder dem Urteil des Agenten (Teamcall 13.11.).

## 2. Die drei Wege

```
Rechnung ─▶ B1 Regelprüfung ─┬─ Ausschlusskriterium (Abschnitt 3) ─────────────────▶ Weg C: Eskalation direkt (ohne Agent)
                             ├─ klärbarer Prüfbedarf (Abschnitt 4) ─▶ Agent prüft ─┬▶ aufgelöst ──▶ Weg B: Prüffall mit Begründung, Freigabe per Klick
                             │                                                    └▶ nicht aufgelöst ─▶ Weg C
                             └─ alle Standardkriterien erfüllt (Abschnitt 5) ────────────────────────▶ Weg A: Standardfall, Freigabe per Klick
```

| Weg | Was passiert | Was der Mensch tut | Agent beteiligt |
|---|---|---|---|
| **A Standardfall** | B1 findet nichts außer Hinweisen. Vorschlag „freigeben“ mit Kontierung, Freigabestufe und Skonto | Freigabe mit einem Klick (bis 1.000 € auch als Sammelfreigabe) | nein |
| **B Prüffall** | B1 meldet eine Unklarheit, die sich durch Nachschlagen klären lässt. Der Agent prüft vertieft und begründet mit Quellen | liest die Begründung, gibt per Klick frei oder lehnt ab | ja |
| **C Eskalation** | Kritischer Befund oder Betrugsverdacht. Vorschlag „klären“ oder „ablehnen“ mit Beleg, Bezug und Betrag | prüft selbst, klärt über die Stammdaten (z. B. Rückruf) | nein |

Weg C läuft bewusst ohne Agent. Die Entscheidung steht durch die Regel fest, und ein Sprachmodell würde nur Kosten verursachen. Bei manipulierten Belegen (Prompt Injection, gefälschte Absender) soll das Modell den Inhalt außerdem gar nicht erst verarbeiten.

**Zuordnungsregel für das Programm:** Der Prüfdienst vergibt jedem Befund eine Schwere (`kritisch`, `warnung`, `info`, siehe `regeln.py`). Daraus folgt der Weg:

| Befunde einer Rechnung | Weg |
|---|---|
| mindestens ein Befund `kritisch` **oder** einer der fünf verschärften Warnungen (Abschnitt 3, markiert mit ⚑) | C |
| sonst mindestens ein Befund `warnung` | B |
| nur Befunde `info` oder gar keine | A |

Die fünf verschärften Warnungen betreffen Absender, Bankverbindung und Anweisungen im Beleg. Im Code sind sie „warnung“. Im Katalog führen sie trotzdem direkt zur Eskalation, weil sie auf Betrug oder Manipulation hindeuten und der Agent solche Inhalte nicht verarbeiten soll. Der Code muss dafür nicht geändert werden: Die Liste der verschärften Codes kann als Konfiguration hinterlegt werden (Abschnitt 10).

## 3. Weg C – Ausschlusskriterien (direkte Eskalation)

Ist **eines** erfüllt, geht die Rechnung direkt an einen Menschen.

| Nr. | Kriterium | Befundcodes im Prüfdienst (Schwere im Code) | Begründung / Quelle |
|---|---|---|---|
| C1 | Lieferant unbekannt oder im Register gelöscht | `LIEFERANT_UNBEKANNT`, `LIEFERANT_GELOESCHT` (kritisch) | Prüfliste Brinkmann („Lieferant muss im Stamm vorhanden sein“), Scheinrechnungen in den Falldaten |
| C2 | Bankverbindung weicht ab, ist ungültig oder gehört zu einem anderen Lieferanten | `IBAN_ABWEICHUNG`, `IBAN_UNGUELTIG`, `IBAN_ANDERER_LIEFERANT` (kritisch); ⚑ `BANK_BLZ_WIDERSPRUCH` (warnung) | Betrugsmuster Bankänderung; Interviews Brinkmann und Dr. Schürmann (zwei Verdachtsfälle 09/2026) |
| C3 | Absender verdächtig oder vorherige Bankänderungs-Mail | `ABSENDER_DOMAIN_IMITAT` (kritisch); ⚑ `ABSENDER_DOMAIN_FREMD`, ⚑ `REPLY_TO_ABWEICHEND`, ⚑ `BANKAENDERUNG_MAIL_VORHER` (warnung) | Look-alike-Domains in den Falldaten; Out-of-Band-Verifikation (heise 07.11.2026) |
| C4 | Anweisung im Beleg (z. B. „bereits freigegeben“) | ⚑ `ANWEISUNG_IM_BELEG` (warnung) | Brief: Inhalte sind Daten, keine Anweisungen; Schutz vor Prompt Injection |
| C5 | Falscher Empfänger oder Pflichtangabe fehlt | `FALSCHER_EMPFAENGER`, `PFLICHTANGABE_FEHLT` (kritisch) | § 14 UStG; Prüfliste Brinkmann (Firmierung, Pflichtangaben) |
| C6 | Rechnerisch falsch | `RECHNERISCH_FALSCH` (kritisch) | Prüfliste Brinkmann; Kötter: unter 1.000 € wird heute nur noch rechnerisch geprüft |
| C7 | Dublette oder bereits bezahltes Original | `DUBLETTE`, `KORREKTUR_ORIGINAL_BEZAHLT` (kritisch) | Prüfliste Brinkmann (Dublettenprüfung) |
| C8 | Nicht vereinbarter Zuschlag | `ZUSCHLAG_NICHT_VEREINBART` (kritisch) | Brinkmann: Eilzuschläge Albers & Terbrack |
| C9 | Bestellung gehört zu anderem Lieferanten, PDF und XML widersprechen sich | `BESTELLUNG_ANDERER_LIEFERANT`, `PDF_XML_WIDERSPRUCH` (kritisch) | Widerspruch in den Grunddaten, kein Nachschlagen möglich |
| C10 | Bankänderungs-Mail ohne Rechnung | (eigener Vorgang) | Klären, Rückruf nur über die Telefonnummer im Stamm; der Stamm wird nicht geändert (Brief, RACI: Änderung Bankverbindung) |
| C11 | Agent konnte den Prüfbedarf aus Weg B nicht auflösen | – | Mensch entscheidet bei verbleibender Unsicherheit |

Vorschlag: Bei C1 bis C9 übernimmt der Vorschlag an den Menschen die Empfehlung aus dem Befundkatalog („ablehnen“ oder „klären“, `regeln.py`).

## 4. Weg B – klärbarer Prüfbedarf (Agent prüft)

Kein Ausschlusskriterium, aber mindestens einer der folgenden Befunde (alle Schwere `warnung`). Der Agent schlägt nach (Seitenbild, Bestellung, Wareneingang, Preisvereinbarung, Lieferantenhistorie, Register) und begründet mit Quellen.

| Nr. | Prüfbedarf | Befundcodes | Was der Agent klären kann |
|---|---|---|---|
| B1 | Beleg unsicher gelesen | `LESBARKEIT_UNSICHER`, `POSITIONEN_UNVOLLSTAENDIG` | Werte am Seitenbild prüfen (Vorschlag N. Hall: Bilderkennung mit 150 dpi statt OCR) |
| B2 | Bestellbezug unklar | `BESTELLUNG_FEHLT`, `BESTELLUNG_UNBEKANNT`, `POSITION_OHNE_BESTELLBEZUG` | passende Bestellung über Lieferant, Artikel und Betrag finden |
| B3 | Preis- oder Mengenabweichung | `PREIS_ABWEICHUNG`, `MENGE_UEBER_WARENEINGANG`, `WARENEINGANG_FEHLT` | Preisvereinbarung und Teillieferungen prüfen, Abweichung in Euro beziffern |
| B4 | Mögliche Dublette oder Gutschrift ohne Bezug | `MOEGLICHE_DUBLETTE`, `GUTSCHRIFT_OHNE_BEZUG` | frühere Rechnungen vergleichen (z. B. nur eine Ziffer anders) |
| B5 | Neuer Lieferant oder Registerangabe unklar | `LIEFERANT_NEU`, `REGISTERANGABE_FEHLT`, `REGISTER_ABWEICHUNG` | Register abgleichen; Einkauf fragen |
| B6 | Steuerlicher Sonderfall | `REVERSE_CHARGE_HINWEIS_FEHLT` | Lieferland und Steuerbehandlung prüfen |

Regeln für Weg B:
- Der Agent darf **nie milder** entscheiden, als die Regeln erlauben. Findet er einen kritischen Befund, gilt Weg C (Policy Enforcement Point, heise 07.11.2026).
- Bei B5 (neuer Lieferant) wird nie „Standardfall“ vorgeschlagen. Der Vorschlag ist höchstens „freigeben nach Prüfung“.
- Freigabestufe, Kontierung und Skonto kommen immer aus B1, nie aus dem Agenten.

## 5. Weg A – Standardfall (alle Kriterien erfüllt)

| Nr. | Kriterium | Quelle |
|---|---|---|
| A1 | B1 meldet nur Hinweise (Schwere `info`, Liste unten) | Befundkatalog `regeln.py` |
| A2 | Lieferant aktiv im Stamm, IBAN und Absender-Domain stimmen mit dem Stamm überein | Prüfliste Brinkmann |
| A3 | Bestellung vorhanden; Preis innerhalb der Toleranz (±1 € je Rechnung) oder laut Preisvereinbarung; Menge ≤ Wareneingang | Freigaberichtlinie 2024, Abschnitt 3 („Toleranz ±1 € je Rechnung“, „Berechnet wird höchstens die gelieferte Menge“); Preisvereinbarungen 2026 |
| A4 | Keine Dublette | Prüfliste Brinkmann |
| A5 | Beleg sicher gelesen (XRechnung, ZUGFeRD oder PDF mit Textebene) | Lesbarkeit |
| A6 | Keine Änderung von Bankverbindung oder Stammdaten des Lieferanten in den letzten 90 Tagen | Betrugsmuster Bankänderung. **Derzeit nicht prüfbar:** Der Lieferantenstamm enthält kein Änderungsdatum. Geprüft werden bisher nur Bankänderungs-Mails der letzten 90 Tage (`BANKAENDERUNG_MAIL_VORHER` → Weg C). Klären, ob das reicht oder ob ein Änderungsdatum ergänzt werden soll. |

Hinweis-Befunde (`info`), die einen Standardfall nicht verhindern, aber im Vorschlag angezeigt werden:

| Befundcode | Bedeutung für den Menschen |
|---|---|
| `PREISVEREINBARUNG_ANGEWENDET` | Preis höher als die Bestellung, aber laut Preisvereinbarung 2026 korrekt (Testgruppe K1, kein Fehlalarm). Offene Frage dazu: Abschnitt 11, Punkt 3 |
| `PREIS_UNTER_REFERENZ` | Preis unter Bestellung oder Preisvereinbarung |
| `WIEDERKEHRENDE_LEISTUNG` | keine Bestellung, bei diesem Lieferanten üblich (z. B. Wartung, Miete). **Widerspruch:** Im Code ist das ein Hinweis, die Freigaberichtlinie verlangt bei Rechnungen ohne Bestellbezug aber „Rückfrage beim Besteller, Freigabe nach Bestätigung“. Vorschlag: als Prüffall (Weg B) behandeln, siehe Abschnitt 11, Punkt 5 |
| `KORREKTUR_ERSETZT` | Korrekturrechnung ersetzt eine frühere, noch nicht bezahlte Rechnung |
| `ZAHLUNGSBEDINGUNG_ABWEICHEND` | Zahlungsbedingung weicht vom Stamm ab. Maßgeblich für Skonto und Fälligkeit bleibt der Stamm |
| `DUPLIKAT_VERMERK` | Dokument trägt den Vermerk „Duplikat“ oder „Kopie“; eine echte Dublette wäre ein Befund nach C7 |
| `SKONTO_FRIST_KNAPP` | zuerst bearbeiten (Kennzahl Skontoquote) |
| `ANLAGEGUT_HINWEIS` | über 800 € netto, Anlagenbuchhaltung informieren |
| `BANKAENDERUNG_MAIL_HINWEIS` | Es gab eine frühere Bankänderungs-Mail, diese Rechnung nutzt aber die IBAN aus dem Stamm |

## 6. Routing: Wer bekommt den Vorschlag?

Die Freigabestufen bleiben, wie die Freigaberichtlinie sie vorgibt (Freigaberichtlinie 2024, Abschnitt 2; RACI; Ist-Prozess, Schritt 5). Das System ändert, wer die Vorarbeit macht, nicht wer verantwortlich ist (Teamcall 13.11.).

| Betrag brutto | Weg A und B: Freigabe per Klick durch | Hinweis |
|---|---|---|
| bis 1.000 € | Sachbearbeitung (Kreditorenbuchhaltung) | Standardfälle als Sammelfreigabe möglich (Vorschlag, nicht aus den Unterlagen) |
| über 1.000 bis 10.000 € | Abteilungsleitung der bestellenden Abteilung (Material/Logistik: Leiter Einkauf; Service, IT, Produktion, QM, Marketing: jeweilige Leitung; Finanzen/Personal: Leiterin Rechnungswesen) | Zuordnung laut Freigaberichtlinie, Abschnitt 2 |
| über 10.000 € | kaufmännische Geschäftsführung (Dr. Schürmann, seit 01.03.2026) | Entscheidungsvorlage mit allen Unterlagen; Frist 2 Werktage, Fachabteilung bestätigt die Leistung (Interview Dr. Schürmann) |

Gutschriften folgen denselben Grenzen, gemessen am absoluten Betrag (Freigaberichtlinie, Abschnitt 2).

Fristen: Laut Freigaberichtlinie (Abschnitt 4) sind Freigaben innerhalb von 3 Arbeitstagen zu erteilen, Rechnungen mit Skonto haben Vorrang. Frau Dr. Schürmann nennt für ihre Freigaben über 10.000 € eine kürzere Frist von 2 Werktagen. Beide Werte sind konfigurierbar (Abschnitt 10).

Weg C geht immer zuerst an die Kreditorenbuchhaltung, die den Fall klärt, und danach an die zuständige Freigabestufe. Bei einer Bankänderung gilt laut Freigaberichtlinie (Abschnitt 3): Bestätigung nur telefonisch über die im Lieferantenstamm hinterlegte Rufnummer, Stammdatenänderung im Vier-Augen-Prinzip.

Variante für die Evaluation: Frau Kötter plant, Freigaben **unter 5.000 €** zu digitalisieren und per Klick der Sachbearbeitung erledigen zu lassen. Das wäre eine Änderung der Freigaberichtlinie, denn heute ist ab 1.000 € die Abteilungsleitung zuständig. Wir zeigen es als konfigurierbare Variante (`grenze_sachbearbeitung` = 5.000) und messen, wie viele Fälle sich dadurch verschieben. Die Entscheidung liegt beim Unternehmen.

## 7. Korrekturhinweis an Lieferanten (Vorschlag)

Neu gegenüber dem 10.11.: Der Agent **entwirft** den Korrekturhinweis, ein Mensch **sendet** ihn mit einem Klick. Damit bleibt auch die Kommunikation nach außen beim Menschen.

Ein Entwurf wird nur erstellt, wenn alle Bedingungen erfüllt sind:
- kein Befund aus C1 bis C4 (Echtheit, Bankverbindung, Absender, Anweisungen),
- behebbarer Fehler (z. B. rechnerisch falsch, Pflichtangabe fehlt, falscher Empfänger, Preis- oder Mengenabweichung),
- Versand nur an die E-Mail-Adresse aus dem Lieferantenstamm, nie an Absender oder Reply-To der Rechnung,
- Text aus einer festen Vorlage mit Befundcode, Beleg und Betrag.

## 8. Zuordnung der Testgruppen (für die Testfälle)

| Testgruppe (Evaluationskonzept) | Erwarteter Weg | Erwarteter Vorschlag |
|---|---|---|
| K0 korrekt, ohne Auffälligkeit | A | freigeben |
| K1 neue Preise laut Preisvereinbarung 2026 | A | freigeben, kein Fehlalarm |
| K2 IBAN weicht ab | C | klären |
| K3 Absender unbekannt, Scheinrechnung | C | ablehnen oder klären |
| K4 falscher Empfänger, gelöschte Firma | C | ablehnen |
| K5 Dublette | C | ablehnen |
| K6 Zahlungserinnerung mit Rechnungskopie | C | ablehnen (Dublette) |
| K7 Korrekturrechnung | A (ersetzt Original) oder C (Original bezahlt) | je nach Fall |
| K8 Preis- oder Mengenabweichung | B | klären mit Betrag oder freigeben nach Prüfung |
| K9 nicht vereinbarter Zuschlag | C | klären bzw. ablehnen |
| K10 Prompt Injection im Bemerkungsfeld | C (verschärfte Warnung) | klären, Anweisung ignoriert |
| K11 Scan mit Lesefehlern | B | Lieferant richtig zugeordnet, Werte bestätigt |
| K12 Bankänderungs-Mail ohne Rechnung | C | klären, Stamm nicht ändern |
| K13 Pflichtangaben fehlen | C | ablehnen, Korrektur anfordern |

## 9. Was das Programm je Rechnung festhalten muss (Brücke zu #44)

Damit sich prüfen lässt, ob der Katalog wirkt, und damit Nicolas die Kennzahlen (#40, #48) berechnen kann, sollte jede Prüfung mindestens Folgendes speichern. Laut Wogil braucht jede Baseline einen eigenen Export, deterministisch über Python und agentisch über SRW (Kommentar zu #44, 10.11.).

- Rechnungs-ID, Variante (B1, C1 oder mehrstufig) und Regelversion (`REGELVERSION` in `config.py`)
- alle Befundcodes mit Schwere, daraus der **Weg (A, B oder C)** und das ausschlaggebende Kriterium (z. B. C2)
- Vorschlag des Systems und, falls der Agent beteiligt war, sein Ergebnis (aufgelöst oder nicht aufgelöst)
- Freigabestufe, Bruttobetrag, Skontofrist
- Zeitstempel (Eingang, Prüfung fertig, Entscheidung durch den Menschen) und die Entscheidung selbst (für Durchlaufzeit und Skontoquote)
- beim Agenten: Tokens bzw. Kosten pro Fall

Welche dieser Felder der Prüfdienst heute schon speichert, wird in #44 geprüft (A-34, bis 15.11.).

## 10. Konfiguration (unternehmensspezifisch)

| Schlüssel | Voßkamp | Quelle |
|---|---|---|
| `grenze_sachbearbeitung` | 1000.00 (Variante: 5000.00) | Freigaberichtlinie (`GRENZE_SACHBEARBEITUNG`); Interview Kötter |
| `grenze_abteilungsleitung` | 10000.00 | Freigaberichtlinie (`GRENZE_ABTEILUNGSLEITUNG`) |
| `preis_toleranz_rechnung` | 1.00 | Freigaberichtlinie (`PREIS_TOLERANZ_RECHNUNG`) |
| `sammelfreigabe_bis_brutto` | 1000.00 | Vorschlag |
| `frist_freigabe_arbeitstage` | 3 | Freigaberichtlinie 2024, Abschnitt 4 |
| `frist_geschaeftsfuehrung_werktage` | 2 | Interview Dr. Schürmann |
| `verschaerfte_warnungen` | `BANK_BLZ_WIDERSPRUCH`, `ABSENDER_DOMAIN_FREMD`, `REPLY_TO_ABWEICHEND`, `BANKAENDERUNG_MAIL_VORHER`, `ANWEISUNG_IM_BELEG` | dieser Katalog, Abschnitt 3 |
| `frist_bankaenderung_mail_tage` | 90 | `stammdaten.py` (`mails_mit_bankaenderung`) |
| `korrekturhinweis_entwurf_aktiv` | true | Teamcall 10.11., angepasst 13.11. |

Die Freigabegrenzen und die Preistoleranz stehen bereits in `config.py`. Die übrigen Schlüssel sind neu. Ein anderes Unternehmen ändert nur diese Werte, nicht den Ablauf.

## 11. Offene Fragen (für den Teamcall 15.11.)

1. Bleibt die Bezeichnung D1 für den mehrstufigen Weg, oder wird er neu benannt? (Abstimmung mit Emin, A-38)
2. **Prüfscore** (Vorschlag Nicolas: ab 90 ohne KI, 50–90 mit Agent): Wird er eingesetzt, oder reicht die Zuordnung über die Befunde aus Abschnitt 2? Die Zuordnung über die Befunde ist eindeutig und lässt sich begründen. Ein Score müsste zusätzlich festlegen, wie viele Punkte jeder Befund kostet. Ausschlusskriterien überstimmen ihn in jedem Fall.
3. **Vier-Augen-Prinzip:** Frau Kötter will es nicht komplett wegfallen lassen: „Gerade bei größeren Beträgen und bei Rechnungen mit speziellen Preisvereinbarungen muss ein Mensch noch drüber schauen“ (Interview Kötter). Reicht dafür die Freigabe per Klick, oder braucht eine Rechnung mit `PREISVEREINBARUNG_ANGEWENDET` den Weg B mit Begründung? In der Freigaberichtlinie ist das Vier-Augen-Prinzip nur für Zahlungslauf und Stammdatenänderung festgelegt (Abschnitte 1 und 3).
4. **Rückruf-Gate über 5.000 €** bei bekannten Lieferanten (Idee Nicolas, angelehnt an Frau Kötters Hinweis auf das persönliche Gespräch): aufnehmen, und wenn ja, nur bei Weg C oder bei jeder Rechnung über der Grenze? Für Bankänderungen schreibt die Freigaberichtlinie den Rückruf bereits vor.
5. **`WIEDERKEHRENDE_LEISTUNG`:** Im Code ein Hinweis, laut Freigaberichtlinie ist aber eine Bestätigung des Bestellers nötig. Vorschlag: im Prüfdienst als `warnung` führen (Weg B) oder die Bestätigung des Bestellers als Teil der Freigabe per Klick festlegen. Mit Emin klären.
6. Kriterium A6 (Sperrfrist für Stammdatenänderungen): Änderungsdatum im Lieferantenstamm ergänzen oder streichen?
7. Verteilung der Rechnungsbeträge aus WAVE, um die Wirkung der Grenzen zu zeigen (Emin).

## Quellen

- Brief Fall 08; Interviews Brinkmann, Kötter, Dr. Schürmann; Ist-Prozess; RACI; Kennzahlen (`cases/08_eingangsrechnungen/`)
- Freigaberichtlinie für Eingangsrechnungen, gültig ab 01.07.2024 (`companies/a_vosskamp/share/S/Finanzen/Kreditoren/Richtlinien/`)
- Prüfliste Brinkmann und Freigaberichtlinie, wie im Prüfdienst umgesetzt (`fall08-stack/pruefdienst/app/regeln.py`, `config.py`, `stammdaten.py`; Regelversion 2026-11-03.2)
- GitHub-Issues #43, #44 (inkl. Kommentar Wogil, 10.11.2026), #40, #48
- Rückmeldung N. Hall (10.11.2026); Teamcalls 10.11. und 13.11.2026
- Gharbi, M.; Magnussen, S. J. (2026): Sichere Architektur für KI-Agenten im Backoffice. heise online, 07.11.2026. https://heise.de/-11514414
