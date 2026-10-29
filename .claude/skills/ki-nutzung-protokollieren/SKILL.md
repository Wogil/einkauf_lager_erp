---
name: "ki-nutzung-protokollieren"
description: "Am Ende eines Chats mit Projektbezug (Projektmodul WiSe 2026/27) die KI-Nutzung erfassen und als Eintrag in docs/ki-nutzung.md im Projekt-Repo eintragen."
---

# KI-Nutzung protokollieren

## Warum es diesen Skill gibt

Im Projektmodul (Prof. Trost, WiSe 2026/27) verlangt die Eigenständigkeitserklärung:

1. jedes verwendete KI-Tool mit Produktname, Anbieter und URL,
2. eine **vollständige Übersicht**, wofür die KI genutzt wurde,
3. die **Kennzeichnung** übernommener KI-Inhalte in Dokumentation und Code.

Der Dozent will die Nutzung sehr genau dokumentiert sehen. Außerdem fließt das Protokoll ins **Self Assessment** ein, also die kritische Reflexion der eigenen Projektarbeit: Wo hat KI geholfen, wo lag sie falsch, was hat das Team selbst geprüft und entschieden.

Das Protokoll liegt im Team-Repo unter `docs/ki-nutzung.md`. Jedes Teammitglied führt diesen Skill am Ende jedes Chats mit Projektbezug aus.

## Was protokolliert wird und was nicht

- **Ja:** KI als Werkzeug für die Projektarbeit, also Recherche, Analyse der Falldaten, Anforderungsanalyse, Konzeption, Textentwürfe, Code-Assistenz, Reviews, sprachliche Überarbeitung, Übersetzungen.
- **Nein:** das LLM, das Teil unserer Lösung ist (der Agent auf SRW). Das ist das Produkt und gehört in die technische Doku.
- **Nein:** Chats ohne Projektbezug. Gibt es im ganzen Chat keinen Projektbezug, sag das und brich ab.

## Ablauf

### 1. Chat auswerten

Geh den **gesamten** bisherigen Chat durch und bestimme die einzelnen Nutzungen. Eine Nutzung ist ein zusammenhängender Zweck, zum Beispiel „Fallvergleich“, „Prompt-Entwurf für den Agenten“ oder „Kapitel 2 sprachlich überarbeitet“. Mehrere Zwecke ergeben mehrere Einträge. Lege nicht für jede Nachricht einen eigenen Eintrag an.

Halte für jede Nutzung fest:

- **Kategorie**, eine von: Recherche · Datenanalyse/Orientierung · Anforderungsanalyse · Konzeption/Architektur · Code-Erstellung · Code-Review/Debugging · Textentwurf · Sprachliche Überarbeitung · Übersetzung · Evaluation/Tests · Projektorganisation
- **Was die KI gemacht hat:** ein bis drei Sätze, konkret und ohne Werbesprache
- **An die KI gegebene Daten:** hochgeladene Dateien, freigegebene Ordner, URLs. Wichtig, weil Teile der Falldaten als vertraulich markiert sind.
- **Fehler und Grenzen der KI:** Stellen, an denen die KI falsch lag, korrigiert werden musste, etwas erfunden hat oder nur vermutet hat. Ehrlich aufnehmen, das ist Material fürs Self Assessment. Wenn nichts davon vorkam: „–“.

### 2. Fehlende Angaben erfragen

Erfinde nichts. Frag die Person in **einer** Nachricht nach allem, was sich aus dem Chat nicht sicher ergibt:

- Name und Kürzel (z. B. „Emin Feldmann, EF“), falls nicht bekannt
- Link zum Chat bzw. zur Sitzung, falls du ihn nicht kennst
- **Übernahme** je Nutzung, also was mit dem Ergebnis passiert ist oder passieren soll:
  - `nicht übernommen`
  - `als Arbeitsgrundlage` (Ideen oder Struktur, Text bzw. Code selbst geschrieben)
  - `teilweise übernommen`
  - `wörtlich übernommen`
- **Fundstelle**, falls übernommen: Datei, Kapitel, Commit
- **Prüfung:** Wie hat die Person das Ergebnis geprüft (gegen Daten, Folien oder Tests)? Wenn noch nicht geprüft: „offen“ und was zu prüfen ist.

Tool und Modell trägst du selbst ein: Produktname, Anbieter, URL und das Modell, unter dem du läufst, soweit bekannt. Wenn du das Modell nicht sicher kennst, schreib „Modell nicht bekannt“.

### 3. Einträge formulieren und bestätigen lassen

Nutze **exakt** dieses Format, ein Block pro Nutzung:

```markdown
### KI-JJJJMMTT-KÜRZEL-n · <kurzer Titel>
- **Datum:** TT.MM.JJJJ
- **Person:** <Vorname Nachname>
- **Tool:** <Produkt> (<Anbieter>, <URL>), Modell: <Modell>
- **Chat/Sitzung:** <Link>
- **Phase:** <Meilenstein oder Projektphase, z. B. Vorbereitung Initial Review (03.11.)>
- **Kategorie:** <Kategorie>
- **Was die KI gemacht hat:** <1–3 Sätze>
- **An die KI gegebene Daten:** <Dateien/Ordner/URLs>
- **Ergebnis/Übernahme:** <Stufe> (<kurze Erläuterung>)
- **Fundstelle:** <Datei/Kapitel/Commit oder „noch keine“>
- **Prüfung durch uns:** <wie geprüft oder „offen: …“>
- **Fehler/Grenzen der KI:** <ehrlich, oder „–“>
```

Regeln für die ID: `n` beginnt pro Person und Tag bei 1. Schau im Protokoll nach, welche Nummern es für dieses Datum und Kürzel schon gibt, und zähl weiter.

Zeig der Person die Einträge und hol eine ausdrückliche Bestätigung oder Korrekturen ein, **bevor** du etwas schreibst. Schreib nie ohne Bestätigung ins Repo.

### 4. Ins Repo eintragen

Wähle den ersten Weg, den die aktuelle Umgebung erlaubt.

**A) Shell mit git verfügbar** (Claude Code, Arbeitsumgebung mit Terminal):

1. Repo finden: Ist das aktuelle Verzeichnis ein git-Repo mit `docs/ki-nutzung.md`, nimm es. Sonst frag nach dem lokalen Pfad oder der Repo-URL und klone sie.
2. `git pull --rebase`, damit Einträge der anderen nicht verloren gehen.
3. Die Einträge **unten** im Abschnitt `## Protokoll` anfügen. Bestehenden Inhalt nicht verändern.
4. Tool-Verzeichnis prüfen: Ist das Tool neu, eine Zeile ergänzen. Ist die Nutzungsart neu, sie in der Spalte „Nutzung/Funktion“ der bestehenden Zeile ergänzen.
5. Nur diese Datei committen: `git add docs/ki-nutzung.md` und `git commit -m "docs(ki): KI-Nutzung <IDs> protokolliert"`.
6. `git push`. Bei einem Konflikt erneut `git pull --rebase` und den Konflikt so lösen, dass **alle** Einträge beider Seiten erhalten bleiben, dann wieder pushen. Bei abgelehntem Push wegen Branch-Schutz: auf einen Branch `ki-log/<kürzel>-<datum>` pushen und einen Pull Request öffnen (falls `gh` verfügbar), sonst der Person den Branch nennen.

**B) GitHub-Connector verfügbar, aber keine Shell:** Die Datei über den Connector lesen, Einträge unten anfügen, Tool-Verzeichnis wie oben aktualisieren und mit derselben Commit-Nachricht speichern.

**C) Weder Shell noch Connector** (z. B. normaler Chat): Gib die bestätigten Einträge als einen Markdown-Codeblock aus. Erkläre in zwei Sätzen, dass die Person sie in `docs/ki-nutzung.md` unten unter `## Protokoll` einfügen und bei einem neuen Tool oder einer neuen Nutzungsart auch das Tool-Verzeichnis ergänzen muss.

### 5. Abschluss

Sag in ein bis zwei Sätzen, was eingetragen wurde (IDs und wohin). Gibt es einen Eintrag mit `teilweise übernommen` oder `wörtlich übernommen`, erinnere daran, die Stelle in Doku oder Code zu kennzeichnen, z. B. mit einer Fußnote „KI-gestützt erstellt, siehe KI-20261029-EF-4“ oder einem Code-Kommentar mit der ID.

## Was du nie tust

- Nutzungen weglassen, beschönigen oder Fehler der KI verschweigen
- Übernahme-Stufen oder Prüfungen erfinden: Wenn die Person nichts dazu sagt, schreib „offen“
- Passwörter, Tokens, API-Keys, personenbezogene Daten oder ganze Chatverläufe ins Protokoll schreiben
- Einträge anderer Teammitglieder ändern oder löschen
- Ohne Bestätigung committen oder pushen