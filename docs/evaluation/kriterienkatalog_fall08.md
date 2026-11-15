# Kriterienkatalog Fall 08 – Welcher Weg für welche Rechnung?

Stand: 15.11.2026 · Fassung 4 · Entwurf: Betül Alkan · Status: Ansatz im Teamcall 15.11. mit dem ganzen Team abgestimmt; Grundlage für die Testfälle (Nicolas, 13.11.-A-36) · Issue: #43

## Änderungen gegenüber Fassung 3 (13.11.) – Ergebnisse des Teamcalls 15.11.
| Nr. | Änderung | Abschnitt | Quelle |
|---|---|---|---|
| Ä1 | Mehrstufiger Ansatz mit Emin abgestimmt (13.11.-A-38 erledigt) | 1 | Protokoll 15.11., Abschnitt 1 |
| Ä2 | **Rechnungen über 10.000 € prüft zusätzlich der Agent** (Weg B, neues Kriterium B7; Weg A nur bis 10.000 €, Kriterium A7) | 2, 4, 5 | Vorschlag Emin, unterstützt von Nicolas; Nutzen in der Evaluation zu belegen |
| Ä3 | **Kein Prüfscore**, Zuordnung nur über die Befunde (offene Frage 2 entschieden) | 2, 11 | Protokoll 15.11., Abschnitt 1 |
| Ä4 | **Skonto-Priorisierung** als eigener Abschnitt | 6 (neu) | Vorschlag Nicolas; Freigaberichtlinie, Abschnitt 4 |
| Ä5 | Routing: Vorbereitung für die Geschäftsführung, Auswertung der Freigabegrenzen 2025, Variante 5.000 € eingeordnet | 7 | Protokoll 15.11., Abschnitt 3 |
| Ä6 | Korrekturhinweis: Versand per Mail erst nach Klick der Sachbearbeitung bestätigt | 8 | Protokoll 15.11., Abschnitt 2 |
| Ä7 | RACI bei Bankänderung präzisiert (Kreditorenbuchhaltung R, Leiterin Rechnungswesen A) | 3 (C10), 7 | RACI; Protokoll 15.11., Abschnitt 2 |
| Ä8 | Testgruppen und Datenfelder um die 10.000-€-Regel ergänzt; neue Konfigurationsschlüssel | 9, 10, 11 | – |
| Ä9 | Offene Fragen aktualisiert (Buchung nach Freigabe, Modell Dr. Schürmann, Rückruf-Gate) | 12 | Protokoll 15.11., offene Punkte |

## 1. Zweck und Grundsätze

Der Katalog legt fest, über welchen Weg eine Rechnung läuft und an wen der Vorschlag geht. Er gilt für den mehrstufigen Ansatz, den Nicolas und Betül am 13.11. vorgeschlagen haben und den das ganze Team am 15.11. trägt (Emin fasste den Ablauf selbst zusammen, keine Einwände).

1. Die **deterministische Prüfung (B1)** prüft jede Rechnung.
2. Der **Agent** prüft, wenn B1 einen klärbaren Prüfbedarf meldet, **und bei jeder Rechnung über 10.000 €** (Teamcall 15.11.).
3. **Ein Mensch entscheidet immer.** Standardfälle gibt er mit einem Klick frei.

Grundsätze:
- **Keine automatische Freigabe und keine automatische Zahlung.** Laut Brief entscheidet die Buchhaltung. Frau Dr. Schürmann sieht rund 90 % der Rechnungen als Standardfälle, „aber das heißt nicht, dass wir sie einfach durchwinken dürfen“. Frau Kötter plant, dass das System prüft und kontiert und die Sachbearbeitung nur noch „Genehmigen“ oder „Ablehnen“ klickt.
- **Die Kriterien prüft der Code, nicht das Sprachmodell.** Das Sprachmodell soll keine Werte oder Geschäftsregeln selbst ableiten (Feedback Initial Review).
- **Ausschlusskriterien gehen vor.** Ein kritischer Befund führt immer direkt zur Eskalation, unabhängig vom Betrag und vom Urteil des Agenten (Teamcall 13.11.).
- **Zuordnung über Befunde, kein Score.** Jeder Weg folgt aus konkreten Befunden und lässt sich damit begründen (Teamcall 15.11.).

## 2. Die drei Wege

```
Rechnung ─▶ B1 Regelprüfung ─┬─ Ausschlusskriterium (Abschnitt 3) ──────────────────────▶ Weg C: Eskalation direkt (ohne Agent)
                             ├─ klärbarer Prüfbedarf (Abschnitt 4, B1–B6) ─┐
                             ├─ Betrag über 10.000 € (Abschnitt 4, B7) ────┴▶ Agent prüft ─┬▶ aufgelöst ──▶ Weg B: Prüffall mit Begründung, Freigabe per Klick
                             │                                                            └▶ nicht aufgelöst ─▶ Weg C
                             └─ alle Standardkriterien erfüllt (Abschnitt 5) ────────────────────────────▶ Weg A: Standardfall, Freigabe per Klick
```

| Weg | Was passiert | Was der Mensch tut | Agent beteiligt |
|---|---|---|---|
| **A Standardfall** | B1 findet nichts außer Hinweisen, Betrag bis 10.000 €. Vorschlag „freigeben“ mit Kontierung, Freigabestufe und Skonto | Freigabe mit einem Klick (bis 1.000 € auch als Sammelfreigabe) | nein |
| **B Prüffall** | B1 meldet eine Unklarheit, die sich durch Nachschlagen klären lässt, oder der Betrag liegt über 10.000 €. Der Agent prüft vertieft und begründet mit Quellen | liest die Begründung, gibt per Klick frei oder lehnt ab | ja |
| **C Eskalation** | Kritischer Befund oder Betrugsverdacht. Vorschlag „klären“ oder „ablehnen“ mit Beleg, Bezug und Betrag | prüft selbst, klärt über die Stammdaten (z. B. Rückruf) | nein |

Weg C läuft bewusst ohne Agent, auch über 10.000 €. Die Entscheidung steht durch die Regel fest, und ein Sprachmodell würde nur Kosten verursachen. Bei manipulierten Belegen (Prompt Injection, gefälschte Absender) soll das Modell den Inhalt außerdem gar nicht erst verarbeiten.

**Zuordnungsregel für das Programm:** Der Prüfdienst vergibt jedem Befund eine Schwere (`kritisch`, `warnung`, `info`, siehe `regeln.py`). Daraus und aus dem Bruttobetrag folgt der Weg (Reihenfolge der Prüfung von oben nach unten):

| Befunde und Betrag einer Rechnung | Weg |
|---|---|
| mindestens ein Befund `kritisch` **oder** eine der fünf verschärften Warnungen (Abschnitt 3, markiert mit ⚑) | C |
| sonst mindestens ein Befund `warnung` **oder** Bruttobetrag über 10.000 € | B |
| sonst (nur Befunde `info` oder keine, Betrag bis 10.000 €) | A |

Die fünf verschärften Warnungen betreffen Absender, Bankverbindung und Anweisungen im Beleg. Im Code sind sie „warnung“. Im Katalog führen sie trotzdem direkt zur Eskalation, weil sie auf Betrug oder Manipulation hindeuten und der Agent solche Inhalte nicht verarbeiten soll. Der Code muss dafür nicht geändert werden: Die Liste der verschärften Codes und die Betragsgrenze für die Agentenprüfung können als Konfiguration hinterlegt werden (Abschnitt 11). Der Export für #44 (`fall08-stack/scripts/kpi_export.sh`, Branch `feature/kpi-export`) setzt diese Regel bereits so um.

**Wirkung der 10.000-€-Regel (nachgerechnet, Daten 2025):** 1.059 von 2.298 Rechnungen lagen über 10.000 € (46,1 %). Weg A ist damit höchstens für 190 + 1.049 = 1.239 Rechnungen möglich, also 1.239 / 2.298 = 53,9 %, rund 54 % (Freigabestufen laut Fallunterlagen, Protokoll 13.11., Abschnitt 5). Das ist eine Obergrenze; Rechnungen bis 10.000 € mit Warnung gehen zusätzlich in Weg B.

## 3. Weg C – Ausschlusskriterien (direkte Eskalation)

Ist **eines** erfüllt, geht die Rechnung direkt an einen Menschen, unabhängig vom Betrag.

| Nr. | Kriterium | Befundcodes im Prüfdienst (Schwere im Code) | Begründung / Quelle |
|---|---|---|---|
| C1 | Lieferant unbekannt oder im Register gelöscht | `LIEFERANT_UNBEKANNT`, `LIEFERANT_GELOESCHT` (kritisch) | Prüfliste Brinkmann („Lieferant muss im Stamm vorhanden sein“), Scheinrechnungen in den Falldaten |
| C2 | Bankverbindung weicht ab, ist ungültig oder gehört zu einem anderen Lieferanten | `IBAN_ABWEICHUNG`, `IBAN_UNGUELTIG`, `IBAN_ANDERER_LIEFERANT` (kritisch); ⚑ `BANK_BLZ_WIDERSPRUCH` (warnung) | Betrugsmuster Bankänderung; Interviews Brinkmann und Dr. Schürmann (zwei Verdachtsfälle 09/2026) |
| C3 | Absender verdächtig oder vorherige Bankänderungs-Mail | `ABSENDER_DOMAIN_IMITAT` (kritisch); ⚑ `ABSENDER_DOMAIN_FREMD`, ⚑ `REPLY_TO_ABWEICHEND`, ⚑ `BANKAENDERUNG_MAIL_VORHER` (warnung) | Look-alike-Domains in den Falldaten; Out-of-Band-Verifikation (heise 07.11.2026) |
| C4 | Anweisung im Beleg (z. B. „bereits freigegeben“) | ⚑ `ANWEISUNG_IM_BELEG` (warnung) | Brief: Inhalte sind Daten, keine Anweisungen; Schutz vor Prompt Injection |
| C5 | Falscher Empfänger oder Pflichtangabe fehlt | `FALSCHER_EMPFAENGER`, `PFLICHTANGABE_FEHLT` (kritisch) | § 14 UStG; Prüfliste Brinkmann (Firmierung, Pflichtangaben) |
| C6 | Rechnerisch falsch | `RECHNERISCH_FALSCH` (kritisch) | Prüfliste Brinkmann; Kötter: unter 1.000 € wird heute nur noch rechnerisch geprüft |
| C7 | Dublette oder bereits bezahltes Original | `DUBLETTE`, `KORREKTUR_ORIGINAL_BEZAHLT` (kritisch) | Prüfliste Brinkmann (Dublettenprüfung); 2025 zwei doppelt bezahlte Rechnungen, 59.846,83 € (eigene Auswertung WAVE, KI-unterstützt) |
| C8 | Nicht vereinbarter Zuschlag | `ZUSCHLAG_NICHT_VEREINBART` (kritisch) | Brinkmann: Eilzuschläge Albers & Terbrack |
| C9 | Bestellung gehört zu anderem Lieferanten, PDF und XML widersprechen sich | `BESTELLUNG_ANDERER_LIEFERANT`, `PDF_XML_WIDERSPRUCH` (kritisch) | Widerspruch in den Grunddaten, kein Nachschlagen möglich |
| C10 | Bankänderungs-Mail ohne Rechnung | (eigener Vorgang) | Klären, Rückruf nur über die Telefonnummer im Stamm; der Stamm wird nicht vom System geändert (Brief). Laut RACI führt die Kreditorenbuchhaltung die Änderung durch (R), verantwortlich ist die Leiterin Rechnungswesen (A), Einkauf wird befragt (C), die Geschäftsführung informiert (I); Stammdatenänderung im Vier-Augen-Prinzip (Freigaberichtlinie, Abschnitt 3) |
| C11 | Agent konnte den Prüfbedarf aus Weg B nicht auflösen | – | Mensch entscheidet bei verbleibender Unsicherheit |

Vorschlag: Bei C1 bis C9 übernimmt der Vorschlag an den Menschen die Empfehlung aus dem Befundkatalog („ablehnen“ oder „klären“, `regeln.py`).

## 4. Weg B – Prüfbedarf (Agent prüft)

Kein Ausschlusskriterium, aber mindestens einer der folgenden Befunde (alle Schwere `warnung`) **oder** ein Bruttobetrag über 10.000 € (B7). Der Agent schlägt nach (Seitenbild, Bestellung, Wareneingang, Preisvereinbarung, Lieferantenhistorie, Register) und begründet mit Quellen.

| Nr. | Prüfbedarf | Befundcodes | Was der Agent klären kann |
|---|---|---|---|
| B1 | Beleg unsicher gelesen | `LESBARKEIT_UNSICHER`, `POSITIONEN_UNVOLLSTAENDIG` | Werte am Seitenbild prüfen (Vorschlag N. Hall: Bilderkennung mit 150 dpi statt OCR) |
| B2 | Bestellbezug unklar | `BESTELLUNG_FEHLT`, `BESTELLUNG_UNBEKANNT`, `POSITION_OHNE_BESTELLBEZUG` | passende Bestellung über Lieferant, Artikel und Betrag finden |
| B3 | Preis- oder Mengenabweichung | `PREIS_ABWEICHUNG`, `MENGE_UEBER_WARENEINGANG`, `WARENEINGANG_FEHLT` | Preisvereinbarung und Teillieferungen prüfen, Abweichung in Euro beziffern |
| B4 | Mögliche Dublette oder Gutschrift ohne Bezug | `MOEGLICHE_DUBLETTE`, `GUTSCHRIFT_OHNE_BEZUG` | frühere Rechnungen vergleichen (z. B. nur eine Ziffer anders) |
| B5 | Neuer Lieferant oder Registerangabe unklar | `LIEFERANT_NEU`, `REGISTERANGABE_FEHLT`, `REGISTER_ABWEICHUNG` | Register abgleichen; Einkauf fragen |
| B6 | Steuerlicher Sonderfall | `REVERSE_CHARGE_HINWEIS_FEHLT` | Lieferland und Steuerbehandlung prüfen |
| **B7** | **Bruttobetrag über 10.000 €** (auch ohne Warnung) | – (Betragsregel, Schlüssel `agent_pruefung_ab_brutto`) | zweite, unabhängige Prüfung der gesamten Rechnung: Historie des Lieferanten, Zahlungsbedingungen, Preisvereinbarung, Bestellbezug und Lieferscheindatum; Entscheidungsvorlage für die Geschäftsführung mit allen Unterlagen |

Begründung B7 (Teamcall 15.11.): Vorschlag Emin, unterstützt von Nicolas. Rechnungen über 10.000 € haben das höhere Risiko; auf sie entfallen 46 % der Rechnungen und rund 91 % des entgangenen Skontos 2025 (eigene Auswertung WAVE 2025, KI-unterstützt; Gegencheck durch Emin per Datenbankabfrage steht aus, 15.11.-A-41). Laut Frau Dr. Schürmann kommen die Unterlagen heute oft unvollständig bei ihr an („fehlt das Lieferschein-Datum oder die Bestellnummer ist nicht verknüpft“), das führt zu Nachfragen und Verzögerung (Interview Dr. Schürmann). B7 ist eine **Hypothese**: In der Evaluation ist gegen B1 zu belegen, ob der Agent bei sauberen Rechnungen über 10.000 € einen Qualitätsunterschied bringt. Wenn nicht, wird B7 über die Konfiguration abgeschaltet (Nicolas, 15.11.).

Regeln für Weg B:
- Der Agent darf **nie milder** entscheiden, als die Regeln erlauben. Findet er einen kritischen Befund, gilt Weg C (Policy Enforcement Point, heise 07.11.2026).
- Bei B5 (neuer Lieferant) wird nie „Standardfall“ vorgeschlagen. Der Vorschlag ist höchstens „freigeben nach Prüfung“.
- Bei B7 ohne weitere Befunde lautet der Regelvorschlag „freigeben“. Der Agent kann ihn nur verschärfen („klären“, „ablehnen“), nicht abschwächen.
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
| **A7** | **Bruttobetrag bis 10.000 €** | Teamcall 15.11. (sonst B7) |

Hinweis-Befunde (`info`), die einen Standardfall nicht verhindern, aber im Vorschlag angezeigt werden:

| Befundcode | Bedeutung für den Menschen |
|---|---|
| `PREISVEREINBARUNG_ANGEWENDET` | Preis höher als die Bestellung, aber laut Preisvereinbarung 2026 korrekt (Testgruppe K1, kein Fehlalarm). Offene Frage dazu: Abschnitt 12, Punkt 2 |
| `PREIS_UNTER_REFERENZ` | Preis unter Bestellung oder Preisvereinbarung |
| `WIEDERKEHRENDE_LEISTUNG` | keine Bestellung, bei diesem Lieferanten üblich (z. B. Wartung, Miete). **Widerspruch:** Im Code ist das ein Hinweis, die Freigaberichtlinie verlangt bei Rechnungen ohne Bestellbezug aber „Rückfrage beim Besteller, Freigabe nach Bestätigung“. Vorschlag: als Prüffall (Weg B) behandeln, siehe Abschnitt 12, Punkt 4 |
| `KORREKTUR_ERSETZT` | Korrekturrechnung ersetzt eine frühere, noch nicht bezahlte Rechnung |
| `ZAHLUNGSBEDINGUNG_ABWEICHEND` | Zahlungsbedingung weicht vom Stamm ab. Maßgeblich für Skonto und Fälligkeit bleibt der Stamm |
| `DUPLIKAT_VERMERK` | Dokument trägt den Vermerk „Duplikat“ oder „Kopie“; eine echte Dublette wäre ein Befund nach C7 |
| `SKONTO_FRIST_KNAPP` | zuerst bearbeiten (Abschnitt 6, Kennzahl Skontoquote) |
| `ANLAGEGUT_HINWEIS` | über 800 € netto, Anlagenbuchhaltung informieren |
| `BANKAENDERUNG_MAIL_HINWEIS` | Es gab eine frühere Bankänderungs-Mail, diese Rechnung nutzt aber die IBAN aus dem Stamm |

## 6. Skonto-Priorisierung (neu, Teamcall 15.11.)

Grundlage: Freigaberichtlinie, Abschnitt 4: „Rechnungen mit Skonto haben Vorrang. Freigaben sind innerhalb von 3 Arbeitstagen zu erteilen.“ 2025 wurden nur 608 von 1.123 Rechnungen mit Skonto rechtzeitig genutzt (54 %), entgangen sind 236.661,87 € (kennzahlen.md). Vorschlag Nicolas, Zustimmung Betül (Teamcall 15.11.).

| Regel | Inhalt | Quelle |
|---|---|---|
| S1 Kennzeichen | Jeder Vorschlag mit Skonto zeigt oben Skontobetrag in Euro und Skontofrist (Datum, verbleibende Arbeitstage). Die Werte berechnet B1 aus der Zahlungsbedingung im Lieferantenstamm, nie der Agent | Freigaberichtlinie, Abschnitt 4; Grundsatz „Regeln vor Agent“; Betül, 15.11. („Skontofrist oben drauf“) |
| S2 Reihenfolge | Offene Vorschläge je zuständiger Person werden nach Skontobetrag absteigend sortiert, statt nach Eingangsdatum | Betül, 15.11. („sortiert nach Skontobetrag“) |
| S3 Frist knapp | Bei `SKONTO_FRIST_KNAPP` steht die Rechnung ganz oben, unabhängig vom Betrag | Befundkatalog `regeln.py`; Vorschlag, im Call nicht besprochen |
| S4 Weg C | Auch bei Eskalation wird die Skontofrist angezeigt, damit die Klärung in der Frist bleibt | Vorschlag; Kötter: telefonisch nachfassen „besonders wenn es um Skonti oder Preisabweichungen geht“ |

Die Priorisierung ändert nicht, **wer** freigibt und **ob** freigegeben wird. Sie ändert nur die Reihenfolge der Vorlage. Wirkung messen: Skontoquote und Durchlaufzeit (Eingang bis Freigabe) im Vergleich zur manuellen Baseline. **Offen** (Nicolas, 15.11.): wie stark sich die Skontobeträge bei den großen Rechnungen unterscheiden; davon hängt ab, wie viel die Sortierung bringt.

## 7. Routing: Wer bekommt den Vorschlag?

Die Freigabestufen bleiben, wie die Freigaberichtlinie sie vorgibt (Freigaberichtlinie 2024, Abschnitt 2; RACI; Ist-Prozess, Schritt 5). Das System ändert, wer die Vorarbeit macht, nicht wer verantwortlich ist (Teamcalls 13.11. und 15.11.). Der Vorschlag geht per Mail direkt an die zuständige Person, niemand muss Rechnungen von Hand weiterreichen (Nicolas, 15.11.).

| Betrag brutto | Weg A und B: Freigabe per Klick durch | Rechnungen 2025 | Hinweis |
|---|---|---|---|
| bis 1.000 € | Sachbearbeitung (Kreditorenbuchhaltung; RACI: R/A) | 190 (8 %) | Standardfälle als Sammelfreigabe möglich (Vorschlag, nicht aus den Unterlagen) |
| über 1.000 bis 10.000 € | Abteilungsleitung der bestellenden Abteilung (Material/Logistik: Leiter Einkauf; Service, IT, Produktion, QM, Marketing: jeweilige Leitung; Finanzen/Personal: Leiterin Rechnungswesen) | 1.049 (46 %) | Zuordnung laut Freigaberichtlinie, Abschnitt 2 |
| über 10.000 € | kaufmännische Geschäftsführung (Dr. Schürmann, seit 01.03.2026; RACI: A) | 1.059 (46 %) | immer Weg B (B7) oder C; Entscheidungsvorlage mit allen Unterlagen, Fachabteilung bestätigt die Leistung (Interview Dr. Schürmann) |

Anzahlen 2025 laut Fallunterlagen (Protokolle 13.11. und 15.11.), Anteile gerundet. Gutschriften folgen denselben Grenzen, gemessen am absoluten Betrag (Freigaberichtlinie, Abschnitt 2).

**Vorbereitung für die Geschäftsführung (Teamcall 15.11.):** Laut eigener Auswertung entfallen 2025 rund 91 % des entgangenen Skontos auf Rechnungen über 10.000 € (215,4 von 236,7 Tsd. €; KI-unterstützt, Gegencheck durch Emin offen). Frau Dr. Schürmann bekommt die Unterlagen „häufig erst nach Ablauf der Skontofrist“ (Interview Dr. Schürmann). Der Hebel ist deshalb, diese Rechnungen am Eingangstag fertig geprüft, mit Begründung des Agenten und mit Skontofrist (Abschnitt 6) bei ihr vorzulegen. Formulierung für Doku und Präsentation: Das System beschleunigt die Vorarbeit; ob schneller freigegeben wird, entscheidet die Geschäftsführung (Betül, 15.11.).

Fristen: Laut Freigaberichtlinie (Abschnitt 4) sind Freigaben innerhalb von 3 Arbeitstagen zu erteilen, Rechnungen mit Skonto haben Vorrang. Frau Dr. Schürmann nennt für ihre Freigaben über 10.000 € eine kürzere Frist von 2 Werktagen; hält sie die Frist nicht ein, soll der Agent eine Entscheidungsvorlage erstellen (Interview Dr. Schürmann). Beide Fristen sind konfigurierbar (Abschnitt 11). Wie B7 (Agent prüft sofort) und dieses Modell (Agent erst nach Fristablauf) zusammenpassen, ist offen (Abschnitt 12, Punkt 6).

Weg C geht immer zuerst an die Kreditorenbuchhaltung, die den Fall klärt, und danach an die zuständige Freigabestufe. Bei einer Bankänderung gilt laut Freigaberichtlinie (Abschnitt 3): Bestätigung nur telefonisch über die im Lieferantenstamm hinterlegte Rufnummer, Stammdatenänderung im Vier-Augen-Prinzip (RACI siehe C10).

**Variante 5.000 € (nur zur Einordnung, nicht Teil der Kernlösung):** Frau Kötter plant, Freigaben unter 5.000 € zu digitalisieren und per Klick der Sachbearbeitung erledigen zu lassen. Das wäre eine Änderung der Freigaberichtlinie, denn heute ist ab 1.000 € die Abteilungsleitung zuständig. Die Auswertung 2025 zeigt: Rechnungen von 1.000 bis 5.000 € machen rund 23 % aus und entlasten damit nur die Abteilungsleitungen; die Geschäftsführung (Grenze 10.000 €) wird nicht entlastet (Teamcall 15.11.). Die Variante bleibt konfigurierbar (`grenze_sachbearbeitung` = 5.000) und kann in der Evaluation gezeigt werden. Die Entscheidung liegt beim Unternehmen.

## 8. Korrekturhinweis an Lieferanten

Bestätigt im Teamcall 15.11.: Der Agent **entwirft** den Korrekturhinweis. Versendet wird er **per Mail erst nach Klick durch die Sachbearbeitung**. Damit bleibt die Kommunikation nach außen beim Menschen.

Ein Entwurf wird nur erstellt, wenn alle Bedingungen erfüllt sind:
- kein Befund aus C1 bis C4 (Echtheit, Bankverbindung, Absender, Anweisungen),
- behebbarer Fehler (z. B. rechnerisch falsch, Pflichtangabe fehlt, falscher Empfänger, Preis- oder Mengenabweichung),
- Versand nur an die E-Mail-Adresse aus dem Lieferantenstamm, nie an Absender oder Reply-To der Rechnung,
- Text aus einer festen Vorlage mit Befundcode, Beleg und Betrag.

## 9. Zuordnung der Testgruppen (für die Testfälle)

| Testgruppe (Evaluationskonzept) | Erwarteter Weg | Erwarteter Vorschlag |
|---|---|---|
| K0 korrekt, ohne Auffälligkeit, bis 10.000 € | A | freigeben |
| **K0-G korrekt, ohne Auffälligkeit, über 10.000 €** (neu) | B (B7) | freigeben; Vergleich B1 vs. mehrstufig zeigt, ob der Agent bei sauberen großen Rechnungen etwas ändert (Fehlalarme, Kosten) |
| K1 neue Preise laut Preisvereinbarung 2026 | A (über 10.000 €: B) | freigeben, kein Fehlalarm |
| K2 IBAN weicht ab | C | klären |
| K3 Absender unbekannt, Scheinrechnung | C | ablehnen oder klären |
| K4 falscher Empfänger, gelöschte Firma | C | ablehnen |
| K5 Dublette | C | ablehnen |
| K6 Zahlungserinnerung mit Rechnungskopie | C | ablehnen (Dublette) |
| K7 Korrekturrechnung | A bzw. B über 10.000 € (ersetzt Original) oder C (Original bezahlt) | je nach Fall |
| K8 Preis- oder Mengenabweichung | B | klären mit Betrag oder freigeben nach Prüfung |
| K9 nicht vereinbarter Zuschlag | C | klären bzw. ablehnen |
| K10 Prompt Injection im Bemerkungsfeld | C (verschärfte Warnung) | klären, Anweisung ignoriert |
| K11 Scan mit Lesefehlern | B | Lieferant richtig zugeordnet, Werte bestätigt |
| K12 Bankänderungs-Mail ohne Rechnung | C | klären, Stamm nicht ändern |
| K13 Pflichtangaben fehlen | C | ablehnen, Korrektur anfordern |

Für die Testfälle (Nicolas): je Testgruppe auch Fälle über 10.000 € aufnehmen, damit sichtbar wird, dass Ausschlusskriterien auch dort direkt zu Weg C führen (kein Agent).

## 10. Was das Programm je Rechnung festhalten muss (Brücke zu #44)

Damit sich prüfen lässt, ob der Katalog wirkt, und damit Nicolas die Kennzahlen (#40, #48) berechnen kann, sollte jede Prüfung mindestens Folgendes speichern. Laut Wogil braucht jede Baseline einen eigenen Export, deterministisch über Python und agentisch über SRW (Kommentar zu #44, 10.11.).

- Rechnungs-ID, Variante (B1, C1 oder mehrstufig) und Regelversion (`REGELVERSION` in `config.py`)
- alle Befundcodes mit Schwere, daraus der **Weg (A, B oder C)** und das ausschlaggebende Kriterium (z. B. C2)
- **neu:** Grund für Weg B getrennt nach Prüfbedarf (B1–B6) und Betragsregel (B7), damit die Evaluation den Nutzen von B7 getrennt auswerten kann
- Vorschlag des Systems und, falls der Agent beteiligt war, sein Ergebnis (aufgelöst oder nicht aufgelöst, verschärft oder bestätigt)
- Freigabestufe, Bruttobetrag, Skontofrist, **Skontobetrag** und **Position in der Reihenfolge** (Abschnitt 6)
- Zeitstempel (Eingang, Prüfung fertig, Entscheidung durch den Menschen) und die Entscheidung selbst (für Durchlaufzeit und Skontoquote)
- beim Agenten: Tokens bzw. Kosten pro Fall (Emin nannte im Call 15.11. für einen Lauf 6 Anfragen für 0,01 €; noch nicht systematisch erfasst)

Stand #44 Stufe 1 (15.11.): Der Export liefert Weg A/B/C bereits mit der 10.000-€-Regel. Für Stufe 2 fehlen der getrennte Grund für Weg B, der Skontobetrag und die Agentenkosten.

## 11. Konfiguration (unternehmensspezifisch)

| Schlüssel | Voßkamp | Quelle |
|---|---|---|
| `grenze_sachbearbeitung` | 1000.00 (Variante: 5000.00) | Freigaberichtlinie (`GRENZE_SACHBEARBEITUNG`); Interview Kötter |
| `grenze_abteilungsleitung` | 10000.00 | Freigaberichtlinie (`GRENZE_ABTEILUNGSLEITUNG`) |
| `agent_pruefung_ab_brutto` | 10000.00 (abschaltbar, z. B. leer) | **neu**, Teamcall 15.11. (B7) |
| `skonto_priorisierung_aktiv` | true | **neu**, Freigaberichtlinie, Abschnitt 4; Teamcall 15.11. |
| `preis_toleranz_rechnung` | 1.00 | Freigaberichtlinie (`PREIS_TOLERANZ_RECHNUNG`) |
| `sammelfreigabe_bis_brutto` | 1000.00 | Vorschlag |
| `frist_freigabe_arbeitstage` | 3 | Freigaberichtlinie 2024, Abschnitt 4 |
| `frist_geschaeftsfuehrung_werktage` | 2 | Interview Dr. Schürmann |
| `verschaerfte_warnungen` | `BANK_BLZ_WIDERSPRUCH`, `ABSENDER_DOMAIN_FREMD`, `REPLY_TO_ABWEICHEND`, `BANKAENDERUNG_MAIL_VORHER`, `ANWEISUNG_IM_BELEG` | dieser Katalog, Abschnitt 3 |
| `frist_bankaenderung_mail_tage` | 90 | `stammdaten.py` (`mails_mit_bankaenderung`) |
| `korrekturhinweis_entwurf_aktiv` | true | Teamcall 10.11., angepasst 13.11., bestätigt 15.11. |

Die Freigabegrenzen und die Preistoleranz stehen bereits in `config.py`. Die übrigen Schlüssel sind neu. Ein anderes Unternehmen ändert nur diese Werte, nicht den Ablauf.

## 12. Offene Fragen

Entschieden am 15.11. (aus Fassung 3): Prüfscore entfällt, Zuordnung über Befunde (frühere Frage 2); Verteilung der Rechnungsbeträge liegt vor, Gegencheck durch Emin offen (frühere Frage 7, jetzt 15.11.-A-41).

1. Bleibt die Bezeichnung **D1** für den mehrstufigen Weg? Die Präsentation für den 17.11. verwendet D1 = mehrstufig; im Team nicht ausdrücklich beschlossen.
2. **Vier-Augen-Prinzip:** Frau Kötter will es nicht komplett wegfallen lassen: „Gerade bei größeren Beträgen und bei Rechnungen mit speziellen Preisvereinbarungen muss ein Mensch noch drüber schauen“ (Interview Kötter). Für große Beträge ist das mit B7 abgedeckt. Offen bleibt, ob eine Rechnung bis 10.000 € mit `PREISVEREINBARUNG_ANGEWENDET` den Weg B braucht. In der Freigaberichtlinie ist das Vier-Augen-Prinzip nur für Zahlungslauf und Stammdatenänderung festgelegt (Abschnitte 1 und 3).
3. **Rückruf-Gate über 5.000 €** bei bekannten Lieferanten (Idee Nicolas, 13.11.): am 15.11. nicht entschieden. Nicolas: kostet Zeit, pflegt aber die Lieferantenbeziehung; Betül: höchstens als Variante zeigen. Für Bankänderungen schreibt die Freigaberichtlinie den Rückruf bereits vor.
4. **`WIEDERKEHRENDE_LEISTUNG`:** Im Code ein Hinweis, laut Freigaberichtlinie ist aber eine Bestätigung des Bestellers nötig. Vorschlag: im Prüfdienst als `warnung` führen (Weg B) oder die Bestätigung des Bestellers als Teil der Freigabe per Klick festlegen. Mit Emin klären (am 15.11. nicht besprochen).
5. Kriterium A6 (Sperrfrist für Stammdatenänderungen): Änderungsdatum im Lieferantenstamm ergänzen oder streichen?
6. **B7 und Modell Dr. Schürmann:** Der Agent prüft nach B7 sofort beim Eingang; Frau Dr. Schürmann sieht die Entscheidungsvorlage des Agenten erst nach Ablauf ihrer Frist von 2 Werktagen vor. Vorschlag: B7 liefert die Vorlage sofort; nach Fristablauf geht eine Erinnerung an die Geschäftsführung. Im Team abstimmen.
7. **Buchung nach der Freigabe:** Emin beschreibt, dass nach allen Freigaben kontiert und gebucht wird (15.11.). Laut Fallvorgaben bleibt das Buchen beim Menschen. Klären, ob das System nach dem Klick nur dokumentiert und die Buchung vorbereitet.
8. **Datenbasis:** Emins Abfrage ergab rund 9.100 Rechnungen (WAVE 5.283, Kolibri 3.440, ArchivPlus 375 nicht gebucht). Ob alle Datensätze Eingangsrechnungen sind, ist offen. Für die Schwellen dieses Katalogs gelten die 2.298 gebuchten Rechnungen 2025.

## Quellen

- Brief Fall 08; Interviews Brinkmann, Kötter, Dr. Schürmann; Ist-Prozess; RACI; Kennzahlen (`cases/08_eingangsrechnungen/`)
- Freigaberichtlinie für Eingangsrechnungen, gültig ab 01.07.2024 (`companies/a_vosskamp/share/S/Finanzen/Kreditoren/Richtlinien/`), Abschnitte 2–4
- Prüfliste Brinkmann und Freigaberichtlinie, wie im Prüfdienst umgesetzt (`fall08-stack/pruefdienst/app/regeln.py`, `config.py`, `stammdaten.py`; Regelversion 2026-11-03.2)
- Export #44 Stufe 1: `fall08-stack/scripts/kpi_export.sh` (Branch `feature/kpi-export`, Stand 15.11.2026)
- Eigene Auswertung WAVE-Export 2025 (Betragsstufen, Skontoverlust, Dubletten; mit Claude Code, 14.–15.11.2026), Folie 4 der Präsentation zum 17.11.
- GitHub-Issues #43, #44 (inkl. Kommentar Wogil, 10.11.2026), #40, #48
- Rückmeldung N. Hall (10.11.2026); Teamcalls 10.11., 13.11. und 15.11.2026 (`05_Meetings_Notizen/`)
- Gharbi, M.; Magnussen, S. J. (2026): Sichere Architektur für KI-Agenten im Backoffice. heise online, 07.11.2026. https://heise.de/-11514414
