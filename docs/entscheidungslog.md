# Entscheidungslog – Team 2

Alle wesentlichen fachlichen und technischen Entscheidungen des Teams. Überholte Entscheidungen bleiben stehen und werden als „ersetzt durch“ markiert, damit nachvollziehbar bleibt, wie sich das Projekt entwickelt hat.

**Status:** gültig · offen (vorläufig, Klärung mit Betreuern ausstehend) · ersetzt

| Nr. | Datum | Entscheidung | Begründung | Status | Quelle |
|---|---|---|---|---|---|
| E-01 | 22.10.2026 | Fokus auf Einkauf & Lager | Passt zum Charakter „Prozess & Transaktion“: Der Agent arbeitet mit Daten und Tools statt nur Texte zu erzeugen; Nutzen ist messbar. | ersetzt durch E-05 | Protokoll Teamcall 22.10. |
| E-02 | 22.10.2026 | Arbeit mit fiktiven Daten der Rehaklinik Küppelsmühle | Daten sollten vom Auftraggeber bereitgestellt werden. | ersetzt durch E-04 | Protokoll Teamcall 22.10. |
| E-03 | 22.10.2026 | GitHub als Planungs- und Versionsumgebung | Meilensteine, Aufgaben, Protokolle, Entscheidungen und Code an einem Ort; Beiträge sind nachvollziehbar. | gültig | Protokoll Teamcall 22.10. |
| E-04 | 29.10.2026 | Zielunternehmen ist ein fiktives KMU ganz ohne ERP-System; das Szenario gestalten wir selbst. Die Rehaklinik entfällt. | Die Szenario-Daten enthalten keine Rehaklinik. Viele KMU arbeiten mit Zetteln, Mails und Chats; ein ERP ist für sie zu teuer und zu aufwendig. | gültig | Notizen 27.10., Teamabstimmung 29.10. |
| E-05 | 29.10.2026 | Die Lösung deckt drei Szenario-Fälle bei Voßkamp ab: 04 Angebot aus Anfrage (Kundenseite), 11 Lieferantenangebote und 08 Eingangsrechnungen (Lieferantenseite). | Deckt beide Seiten des Use Cases ab („Angebotserstellung / Einkauf & Lager“). Die Fälle teilen Lieferanten, Artikel, Bestellungen und Wareneingänge. | offen – Bündelung mit Betreuern klären | Teamabstimmung 29.10. |
| E-06 | 29.10.2026 | Die Voßkamp-Daten dienen nur als Testgrundlage, nicht als Abbild des Zielunternehmens. | Folgt aus E-04: Das Zielunternehmen hat kein ERP. Die Daten liefern realistische Testfälle und die Basis für einen eigenen Lösungsschlüssel. | gültig | Teamabstimmung 29.10. |
| E-07 | 29.10.2026 | Kanäle: E-Mail und Slack/MS Teams. WhatsApp wird nicht angebunden. | E-Mail ist nötig, weil Szenario- und Bewertungsdaten als Mails vorliegen. WhatsApp Business ist zu teuer, aufwendig und datenschutzrechtlich heikel. | gültig | Teamabstimmung 29.10. |
| E-08 | 29.10.2026 | Architektur: Orchestrator verteilt Anliegen an drei Fach-Agenten (Angebot, Lieferanten, Rechnung); jeder Vorschlag wird von einem Menschen freigegeben (Human in the Loop). Kanal-Adapter halten den Kern kanalunabhängig. | Getrennte Prompts, Regeln und Rechte je Fall; getrennte Evaluation. Die Briefs schreiben menschliche Freigabe vor. | gültig | Teamabstimmung 29.10. |
| E-09 | 29.10.2026 | Lager wird als Tool-Schicht umgesetzt (Bestand, Verfügbarkeit, Wareneingang), nicht als eigener Agent. | Bestandsabfragen sind deterministische Rechenarbeit und brauchen kein LLM; es gibt keinen eigenen Lager-Fall mit Musterlösung. | gültig | Teamabstimmung 29.10. |
| E-10 | 01.11.2026 | Datenablage: PostgreSQL mit eigenem, schlankem KMU-Datenmodell. CSV ist nur das Format der Rohdaten. | Die Fälle brauchen Verknüpfungen über mehrere Tabellen; SRW bietet einen Postgres-Connector; große Tabellen gehören nicht in den Kontext des Agenten. | gültig | Teamabstimmung 01.11. |

## Offen (noch keine Entscheidung)

- Plattform: Ist SRW Pflicht, und sind eigene Tools (MCP-Connectoren) freigeschaltet?
- Welcher der drei Fälle wird der Kern mit voller Evaluation?
- Rollenverteilung im Team
