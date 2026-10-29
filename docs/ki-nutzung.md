# KI-Nutzungsprotokoll – Projektmodul WiSe 2026/27 (Team 2)

Dieses Protokoll dokumentiert jede Nutzung von KI-Werkzeugen **während der Projektarbeit**. Es ist die Grundlage für

1. die **Eigenständigkeitserklärung** (Tool mit Produktname und URL, vollständige Übersicht der Nutzung, Kennzeichnung übernommener KI-Inhalte; Vorgabe Trost, Kickoff 15.10.2026, Folie 16),
2. die **Kennzeichnung** von KI-Inhalten in Dokumentation und Code,
3. das **Self Assessment** (kritische Reflexion: wo hat KI geholfen, wo lag sie falsch, was haben wir selbst geprüft und entschieden).

## Regeln

- **Wer trägt ein?** Jede Person nach jeder KI-Sitzung, die Projektbezug hat. Am einfachsten mit dem Skill `ki-nutzung-protokollieren` am Ende des Chats.
- **Was gehört hinein?** KI als *Werkzeug*: Recherche, Analyse, Konzeption, Textentwürfe, Code-Assistenz (Claude, ChatGPT, Copilot, Claude Code, DeepL …).
- **Was gehört nicht hinein?** Das LLM *in* unserer Lösung (der SRW-Agent). Das ist das Produkt und wird in der technischen Dokumentation beschrieben.
- **Ehrlich und knapp.** Keine geschönten Angaben. Fehler der KI und eigene Korrekturen ausdrücklich festhalten, sie sind Material fürs Self Assessment.
- **Keine Geheimnisse.** Keine Passwörter, Tokens oder personenbezogenen Daten ins Protokoll. Keine kompletten Chatverläufe, sondern ein Link reicht.
- **Übernahme-Stufen:** `nicht übernommen` · `als Arbeitsgrundlage` (Ideen/Struktur, eigener Text) · `teilweise übernommen` · `wörtlich übernommen`. Ab *teilweise übernommen* muss die Stelle in Doku oder Code gekennzeichnet werden.
- **IDs:** `KI-JJJJMMTT-KÜRZEL-n`, z. B. `KI-20261029-EF-1`. So entstehen keine Nummernkonflikte zwischen Teammitgliedern.

## Tool-Verzeichnis (für die Eigenständigkeitserklärung)

| KI-Anwendung | Anbieter | Bezugsquelle/URL | Nutzung/Funktion |
|---|---|---|---|
| Claude | Anthropic | https://claude.ai | Analyse der Szenario-Daten und Fallunterlagen; Anforderungsanalyse aus Lehrveranstaltungsfolien; Technologierecherche (SRW); Entwurf von Protokollvorlage und Arbeitsorganisation |

<!-- Neue Tools oder neue Nutzungsarten hier ergänzen. Eine Zeile pro Tool, Nutzungsarten in der letzten Spalte sammeln. -->

## Protokoll

<!-- Neue Einträge immer UNTEN anfügen. Format exakt beibehalten. -->

### KI-20261029-EF-1 · Orientierung in den Szenario-Daten und Fallvergleich
- **Datum:** 29.10.2026
- **Person:** Emin Feldmann
- **Tool:** Claude (Anthropic, https://claude.ai), Modell laut Sitzung: claude-opus-5-5
- **Chat/Sitzung:** https://claude.ai/code/session_01XYoTXgBqnLgnDG82eHgoaT
- **Phase:** Vorbereitung Initial Review (03.11.)
- **Kategorie:** Datenanalyse / Orientierung
- **Was die KI gemacht hat:** Ordnerstruktur der Szenario-Daten (`cases/`, `companies/`, `world/`) ausgewertet und zusammengefasst; Briefs, Prozessunterlagen und Interviews der Fälle 04, 08 und 11 gelesen und verglichen (Ziel, Datenmenge, Messbarkeit, Widersprüche zwischen Interviews und Kennzahlen).
- **An die KI gegebene Daten:** Lesezugriff auf den lokalen Ordner `Projekt/data` (Fallunterlagen, Verzeichnisstruktur, Stichproben aus ERP-README und Laufwerk).
- **Ergebnis/Übernahme:** als Arbeitsgrundlage. Die Fallentscheidung trifft das Team.
- **Fundstelle:** noch keine
- **Prüfung durch uns:** offen. Fallvergleich und genannte Widersprüche gegen die Originaldateien prüfen.
- **Fehler/Grenzen der KI:** Die KI hat einen abgebrochenen Satz („Fall 04, 08 und 11 …“) selbst interpretiert, statt nachzufragen. Die Interpretation wurde im Chat offen benannt.

### KI-20261029-EF-2 · Anforderungsanalyse aus Kickoff- und Szenario-Präsentation
- **Datum:** 29.10.2026
- **Person:** Emin Feldmann
- **Tool:** Claude (Anthropic, https://claude.ai), Modell laut Sitzung: claude-opus-5-5
- **Chat/Sitzung:** https://claude.ai/code/session_01XYoTXgBqnLgnDG82eHgoaT
- **Phase:** Vorbereitung Initial Review (03.11.)
- **Kategorie:** Anforderungsanalyse
- **Was die KI gemacht hat:** Beide Präsentationen (Kickoff Trost, Szenario-Daten) ausgewertet: Ergebnisanforderungen, Meilensteine, Bewertungsrahmen, Messkriterien (versteckte Musterlösung, Baseline, Robustheit …). Widersprüche zwischen den Decks aufgezeigt (Rehaklinik Küppelsmühle vs. Szenario-Fälle, Pflicht zu SRW) und Fragen an die Betreuer formuliert.
- **An die KI gegebene Daten:** `kickoff.pptx`, `Praesentation_Szenario.pdf` (hochgeladen).
- **Ergebnis/Übernahme:** als Arbeitsgrundlage (Fragenliste für die Sprechstunde).
- **Fundstelle:** noch keine
- **Prüfung durch uns:** offen. Abgleich mit den Folien.
- **Fehler/Grenzen der KI:** Die KI hat die 30 Punkte „Self Assessment“ zunächst fälschlich als Nachweis des individuellen Beitrags gedeutet. Emin hat das korrigiert: Gemeint ist die kritische Selbstbewertung der Projektarbeit.

### KI-20261029-EF-3 · Technologierecherche zur Plattform SRW
- **Datum:** 29.10.2026
- **Person:** Emin Feldmann
- **Tool:** Claude (Anthropic, https://claude.ai), Modell laut Sitzung: claude-opus-5-5
- **Chat/Sitzung:** https://claude.ai/code/session_01XYoTXgBqnLgnDG82eHgoaT
- **Phase:** Vorbereitung Initial Review (03.11.)
- **Kategorie:** Technologierecherche / Konzeption
- **Was die KI gemacht hat:** Website und öffentliches GitHub-Repository von SRW (superhuman-remote-worker.com) ausgewertet: Bausteine (Expert, Workspace, Connector, Job), Connector-Typen, Lizenz, Evaluationswerkzeuge. Vorschlag einer Architektur „SRW als Laufzeit + eigener MCP-Service + Postgres“.
- **An die KI gegebene Daten:** URL der Website; öffentliche Quellen.
- **Ergebnis/Übernahme:** als Arbeitsgrundlage. Der Architekturvorschlag ist noch nicht entschieden.
- **Fundstelle:** noch keine
- **Prüfung durch uns:** offen. Klären, welche Funktionen auf der bereitgestellten SRW-Instanz freigeschaltet sind.
- **Fehler/Grenzen der KI:** Die Aussagen beruhen auf öffentlicher Doku, die Hochschulinstanz kann abweichen. Dass die Betreuer den Agenten über die Job-API selbst ausführen, ist eine Vermutung der KI.

### KI-20261029-EF-4 · Organisation der KI-Dokumentation
- **Datum:** 29.10.2026
- **Person:** Emin Feldmann
- **Tool:** Claude (Anthropic, https://claude.ai), Modell laut Sitzung: claude-opus-5-5
- **Chat/Sitzung:** https://claude.ai/code/session_01XYoTXgBqnLgnDG82eHgoaT
- **Phase:** Projektorganisation
- **Kategorie:** Projektorganisation / Vorlagenerstellung
- **Was die KI gemacht hat:** Diese Protokollvorlage entworfen, den Skill `ki-nutzung-protokollieren` geschrieben und einen Text für die Anweisungen des Claude-Projekts entworfen.
- **An die KI gegebene Daten:** Vorgaben aus der Kickoff-Folie 16 (Eigenständigkeitserklärung).
- **Ergebnis/Übernahme:** wörtlich übernommen (diese Datei; Struktur und Regeln von der KI entworfen, vom Team geprüft)
- **Fundstelle:** `docs/ki-nutzung.md`
- **Prüfung durch uns:** offen. Vom Team abnehmen und Format ggf. anpassen.
- **Fehler/Grenzen der KI:** –
