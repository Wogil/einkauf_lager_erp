#!/usr/bin/env python3
"""Erzeugt den Datenstand für den SRW-Agenten als SQLite-Datei (Workaround, solange SRW keine Datenbank erreicht).

Enthält nur, was für die Prüfung von Eingangsrechnungen nötig ist: Einkauf aus WAVE, die Einkaufsdateien des
Altsystems Kolibri (roh, wie exportiert), ArchivPlus-Index, Handelsregister und Bankenverzeichnis.

Mit --stichtag wird der Stand so zurückgeschnitten, wie er am Eingangstag einer Rechnung war. Sonst sähe der
Agent bereits, ob die Rechnung später freigegeben oder bezahlt wurde (Datenleck in der Evaluation).

Aufruf (aus fall08-stack/):
  python3 scripts/srw_datenstand.py                          # voller Stand  -> build/srw/
  python3 scripts/srw_datenstand.py --stichtag 2026-09-24    # Stand am Eingangstag

Ausgabe: vosskamp.sqlite, SCHEMA.md, BEFUNDCODES.md
Nur Python-Standardbibliothek.
"""

import argparse
import csv
import html
import importlib.util
import json
import re
import shutil
import sqlite3
import tempfile
from datetime import date, datetime
from pathlib import Path

HIER = Path(__file__).resolve().parent.parent

WAVE_TABELLEN = [
    "lieferant", "ansprechpartner", "artikel", "ek_preis", "bestellung", "bestellung_position",
    "wareneingang", "wareneingang_position", "eingangsrechnung", "eingangsrechnung_position",
    "zahlungsausgang", "zahlungsausgang_zuordnung", "zahlungslauf", "zahlungsbedingung",
    "sachkonto", "kostenstelle", "mitarbeiter",
]
KOLIBRI_DATEIEN = ["LIEFER", "BESTKOPF", "BESTPOS", "WEKOPF", "WEPOS", "ERKOPF", "ERPOS", "ZAHLAUS",
                   "MIGR_BELEGE", "MIGR_ARTIKEL", "MIGR_KST"]
TYPEN = {"int": "INTEGER", "smallint": "INTEGER", "bigint": "INTEGER", "numeric": "REAL", "decimal": "REAL",
         "real": "REAL", "double": "REAL", "boolean": "TEXT"}


# --------------------------------------------------------------------------- WAVE-Schema lesen
def lies_schema(schema_sql: Path):
    t = schema_sql.read_text(encoding="utf-8")
    tabellen = {}
    for name, rumpf in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", t, re.S):
        spalten = []
        for zeile in rumpf.splitlines():
            m = re.match(r"\s+(\w+)\s+([a-z]+)", zeile)
            if m and m.group(1).upper() not in ("PRIMARY", "CONSTRAINT", "UNIQUE"):
                spalten.append((m.group(1), TYPEN.get(m.group(2), "TEXT")))
        tabellen[name] = {"spalten": spalten, "kommentar": "", "spaltenkommentare": {}}
    for tab, k in re.findall(r"COMMENT ON TABLE (\w+) IS '((?:[^']|'')*)';", t):
        if tab in tabellen:
            tabellen[tab]["kommentar"] = k.replace("''", "'")
    for tab, sp, k in re.findall(r"COMMENT ON COLUMN (\w+)\.(\w+) IS '((?:[^']|'')*)';", t):
        if tab in tabellen:
            tabellen[tab]["spaltenkommentare"][sp] = k.replace("''", "'")
    return tabellen


def wert(v, typ):
    if v is None or v == "":
        return None
    if typ == "INTEGER":
        try:
            return int(v)
        except ValueError:
            return v
    if typ == "REAL":
        try:
            return float(v)
        except ValueError:
            return v
    return v


def lade_wave(con, erp: Path, schema):
    for tab in WAVE_TABELLEN:
        sp = schema[tab]["spalten"]
        typ = dict(sp)
        con.execute(f'CREATE TABLE {tab} ({", ".join(f"{n} {t}" for n, t in sp)})')
        with open(erp / "csv" / f"{tab}.csv", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            spalten = [c for c in r.fieldnames if c in typ]
            zeilen = [[wert(z[c], typ[c]) for c in spalten] for z in r]
        if tab == "ansprechpartner":
            i = spalten.index("lieferanten_nr")
            zeilen = [z for z in zeilen if z[i]]
        con.executemany(f'INSERT INTO {tab} ({",".join(spalten)}) VALUES ({",".join("?" * len(spalten))})', zeilen)


# --------------------------------------------------------------------------- Kolibri (roh)
def lade_kolibri(con, ordner: Path):
    for name in KOLIBRI_DATEIEN:
        p = ordner / f"{name}.CSV"
        with open(p, encoding="cp1252", newline="") as f:
            r = csv.reader(f, delimiter=";")
            kopf = [re.sub(r"\W", "_", k.strip()).lower() or f"spalte{i}" for i, k in enumerate(next(r))]
            zeilen = [z + [""] * (len(kopf) - len(z)) if len(z) < len(kopf) else z[:len(kopf)] for z in r if z]
        tab = f"kolibri_{name.lower()}"
        con.execute(f'CREATE TABLE {tab} ({", ".join(f"{k} TEXT" for k in kopf)})')
        con.executemany(f"INSERT INTO {tab} VALUES ({','.join('?' * len(kopf))})", zeilen)


# --------------------------------------------------------------------------- Referenzdaten
def lade_referenz(con, daten: Path):
    ap = daten / "companies/a_vosskamp/archivplus/Eingangsrechnungen/ArchivPlus_Index_Eingangsrechnungen.csv"
    with open(ap, encoding="utf-8", newline="") as f:
        r = csv.reader(f, delimiter=";")
        kopf = next(r)
        con.execute(f'CREATE TABLE archivplus_index ({", ".join(f"{k} TEXT" for k in kopf)})')
        con.executemany(f"INSERT INTO archivplus_index VALUES ({','.join('?' * len(kopf))})",
                        [[v or None for v in z] for z in r])
    reg = daten / "world/register"
    with open(reg / "index.csv", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        zeilen = list(r)
    con.execute("CREATE TABLE register (firma TEXT, sitz TEXT, registergericht TEXT, registerart TEXT, "
                "registernummer TEXT, status TEXT, auszug_json TEXT)")
    for z in zeilen:
        j = (reg / z["datei"]).with_suffix(".json")
        z["auszug_json"] = j.read_text(encoding="utf-8") if j.exists() else None
    con.executemany("INSERT INTO register VALUES (:firma,:sitz,:registergericht,:registerart,:registernummer,:status,:auszug_json)",
                    zeilen)
    t = html.unescape((daten / "world/banks/README.html").read_text(encoding="utf-8"))
    con.execute("CREATE TABLE bank (blz TEXT, bank TEXT, bic TEXT)")
    for zeile in re.findall(r"<tr>(.*?)</tr>", t, re.S):
        z = [re.sub(r"<[^>]+>", "", x).strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", zeile, re.S)]
        if len(z) >= 4 and re.fullmatch(r"\d{8}", z[2]):
            con.execute("INSERT INTO bank VALUES (?,?,?)", (z[2], z[0], z[3]))


# --------------------------------------------------------------------------- Stichtag
def kolibri_datum(s):
    try:
        return datetime.strptime(s.strip(), "%d.%m.%Y").date().isoformat()
    except (ValueError, AttributeError):
        return None


def schneide(con, s: str):
    """Entfernt alles, was am Stichtag noch nicht bekannt war. Eingangsrechnungen ab Stichtag fallen weg
    (also auch die zu prüfende selbst); Freigaben/Zahlungen nach dem Stichtag werden zurückgesetzt."""
    x = con.execute
    con.create_function("kdat", 1, kolibri_datum)
    # WAVE
    x("DELETE FROM eingangsrechnung WHERE eingangsdatum >= ?", (s,))
    x("UPDATE eingangsrechnung SET freigabe_von_pnr=NULL, freigabe_datum=NULL WHERE freigabe_datum >= ?", (s,))
    x("UPDATE eingangsrechnung SET zahlung_nr=NULL, bezahlt_am=NULL, skonto_genutzt=NULL WHERE bezahlt_am >= ?", (s,))
    x("UPDATE eingangsrechnung SET status = CASE WHEN bezahlt_am IS NOT NULL THEN 'bezahlt' "
      "WHEN freigabe_datum IS NOT NULL THEN 'freigegeben' ELSE 'erfasst' END")
    x("DELETE FROM eingangsrechnung_position WHERE er_nr NOT IN (SELECT er_nr FROM eingangsrechnung)")
    x("DELETE FROM bestellung WHERE bestelldatum > ?", (s,))
    x("UPDATE bestellung SET status=NULL")
    x("DELETE FROM bestellung_position WHERE bestell_nr NOT IN (SELECT bestell_nr FROM bestellung)")
    x("DELETE FROM wareneingang WHERE eingangsdatum > ?", (s,))
    x("DELETE FROM wareneingang_position WHERE we_nr NOT IN (SELECT we_nr FROM wareneingang)")
    # kumulierte Mengen aus dem verbleibenden Stand neu rechnen
    x("""UPDATE bestellung_position SET
           menge_geliefert = (SELECT COALESCE(SUM(wp.menge),0) FROM wareneingang_position wp JOIN wareneingang w
                              ON w.we_nr=wp.we_nr WHERE w.bestell_nr=bestellung_position.bestell_nr
                              AND wp.bestell_pos=bestellung_position.pos),
           menge_berechnet = (SELECT COALESCE(SUM(ep.menge),0) FROM eingangsrechnung_position ep JOIN eingangsrechnung e
                              ON e.er_nr=ep.er_nr WHERE e.bestell_nr=bestellung_position.bestell_nr
                              AND ep.bestell_pos=bestellung_position.pos)""")
    x("DELETE FROM zahlungsausgang WHERE valuta > ?", (s,))
    x("DELETE FROM zahlungsausgang_zuordnung WHERE zahlung_nr NOT IN (SELECT zahlung_nr FROM zahlungsausgang) "
      "OR er_nr NOT IN (SELECT er_nr FROM eingangsrechnung)")
    x("DELETE FROM zahlungslauf WHERE datum > ?", (s,))
    x("DELETE FROM ek_preis WHERE gueltig_ab > ?", (s,))
    # ArchivPlus: Bearbeitungsstand ist nur der heutige, deshalb entfernt
    x("DELETE FROM archivplus_index WHERE eingangsdatum >= ?", (s,))
    x("UPDATE archivplus_index SET workflow_status=NULL, bearbeiter=NULL, er_nr=NULL")
    # Kolibri (Datum TT.MM.JJJJ)
    x("DELETE FROM kolibri_erkopf WHERE kdat(edat) >= ?", (s,))
    x("UPDATE kolibri_erkopf SET freig='', frdat='', stat='' WHERE kdat(frdat) > ?", (s,))
    x("UPDATE kolibri_erkopf SET znr='', bezdat='', skonto='' WHERE kdat(bezdat) > ?", (s,))
    x("DELETE FROM kolibri_erpos WHERE ernr NOT IN (SELECT ernr FROM kolibri_erkopf)")
    x("DELETE FROM kolibri_bestkopf WHERE kdat(dat) > ?", (s,))
    x("UPDATE kolibri_bestkopf SET stat=''")
    x("DELETE FROM kolibri_bestpos WHERE bestnr NOT IN (SELECT bestnr FROM kolibri_bestkopf)")
    x("UPDATE kolibri_bestpos SET gelief='', berech=''")
    x("DELETE FROM kolibri_wekopf WHERE kdat(dat) > ?", (s,))
    x("DELETE FROM kolibri_wepos WHERE wenr NOT IN (SELECT wenr FROM kolibri_wekopf)")
    x("DELETE FROM kolibri_zahlaus WHERE kdat(dat) > ?", (s,))


# --------------------------------------------------------------------------- Doku
def schreibe_schema_md(con, schema, kolibri_doku: str, stichtag, ziel: Path):
    zeilen = ["# Datenstand für die Rechnungsprüfung (Voßkamp Pumpenwerk)", ""]
    zeilen += [f"**Stichtag:** {stichtag}. Der Datenstand entspricht dem Wissen am Eingangstag der zu prüfenden "
               "Rechnung. Spätere Buchungen, Freigaben und Zahlungen sind entfernt." if stichtag else
               "**Stichtag:** keiner (vollständiger Stand, nur für Tests und Exploration)."]
    zeilen += ["", "Abfragen: `sqlite3 vosskamp.sqlite` oder Python (`import sqlite3`). Die Datei ist nur zum Lesen da.", "",
               "## Hinweise", "",
               "- Tabellen ohne Präfix stammen aus dem heutigen ERP **WAVE** (seit Mitte 2024). Beträge in EUR, Datum ISO (JJJJ-MM-TT).",
               "- Tabellen mit Präfix `kolibri_` stammen aus dem **Altsystem Kolibri** (bis 06/2024), **roh wie exportiert**: alle Spalten Text, "
               "Datum TT.MM.JJJJ, Dezimalkomma, teils andere Nummernkreise. Zuordnung alt → neu über `kolibri_migr_*`.",
               "- `lieferant` zeigt den **heutigen** Stammdatenstand (keine Historie). Abweichende Bankverbindungen auf Rechnungen sind deshalb immer zu klären.",
               "- `archivplus_index`: Index des Belegarchivs (was eingegangen ist, mit erkannten Kopfdaten).",
               "- `register`: Handelsregister-Index; `auszug_json` enthält den vollständigen Registerauszug.",
               "- `bank`: Bankleitzahl → Bank und BIC (zur Prüfung der IBAN).", "",
               "## Tabellen", ""]
    for (tab,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"):
        anzahl = con.execute(f"SELECT COUNT(*) FROM {tab}").fetchone()[0]
        spalten = [r[1] for r in con.execute(f"PRAGMA table_info({tab})")]
        info = schema.get(tab, {})
        zeilen.append(f"### `{tab}` ({anzahl} Zeilen)")
        if info.get("kommentar"):
            zeilen.append(info["kommentar"])
        zeilen.append("")
        sk = info.get("spaltenkommentare", {})
        zeilen.append(", ".join(f"`{s}`" + (f" ({sk[s]})" if s in sk else "") for s in spalten))
        zeilen.append("")
    zeilen += ["## Feldbeschreibung Altsystem Kolibri (Originaltext)", "", "```", kolibri_doku.strip(), "```", ""]
    (ziel / "SCHEMA.md").write_text("\n".join(zeilen), encoding="utf-8")


def schreibe_befundcodes(ziel: Path):
    spec = importlib.util.spec_from_file_location("regeln", HIER / "pruefdienst/app/regeln.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    z = ["# Befundcodes", "",
         "Gemeinsame Codes für die deterministische Prüfung (B1) und den Agenten (C1), damit beide Ergebnisse "
         "vergleichbar sind. Passt kein Code, `SONSTIGES` verwenden und den Befund im Text beschreiben.", "",
         "| Code | Schwere | Empfehlung | Bedeutung |", "|---|---|---|---|"]
    for code, (schwere, empf, text) in m.REGELN.items():
        z.append(f"| `{code}` | {schwere} | {empf} | {text} |")
    z.append("| `SONSTIGES` | – | – | Befund ohne passenden Code |")
    (ziel / "BEFUNDCODES.md").write_text("\n".join(z) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--daten", default=str(HIER.parent), help="Szenario-Ordner mit companies/ und world/")
    ap.add_argument("--stichtag", help="JJJJ-MM-TT: Datenstand am Eingangstag der Rechnung")
    ap.add_argument("--ausgabe", default=str(HIER / "build/srw"))
    a = ap.parse_args()
    if a.stichtag:
        date.fromisoformat(a.stichtag)
    daten, ziel = Path(a.daten), Path(a.ausgabe)
    ziel.mkdir(parents=True, exist_ok=True)
    db = ziel / "vosskamp.sqlite"
    tmp = Path(tempfile.mkdtemp()) / "vosskamp.sqlite"   # lokal bauen (Netz-/VM-Laufwerke vertragen kein SQLite-Locking)
    erp = daten / "companies/a_vosskamp/erp"
    schema = lies_schema(erp / "schema.sql")
    con = sqlite3.connect(tmp)
    lade_wave(con, erp, schema)
    lade_kolibri(con, erp / "kolibri_legacy")
    lade_referenz(con, daten)
    for tab, sp in [("eingangsrechnung", "lieferanten_nr"), ("eingangsrechnung", "rechnungsnr_lieferant"),
                    ("eingangsrechnung", "bestell_nr"), ("bestellung", "lieferanten_nr"),
                    ("bestellung_position", "bestell_nr"), ("wareneingang", "bestell_nr"),
                    ("wareneingang_position", "we_nr"), ("eingangsrechnung_position", "er_nr"),
                    ("ek_preis", "artikel_nr"), ("register", "firma")]:
        con.execute(f"CREATE INDEX IF NOT EXISTS ix_{tab}_{sp} ON {tab} ({sp})")
    if a.stichtag:
        schneide(con, a.stichtag)
    con.commit()
    kolibri_doku = (erp / "kolibri_legacy/FELDBESCHREIBUNG.TXT").read_text(encoding="cp1252")
    schreibe_schema_md(con, schema, kolibri_doku, a.stichtag, ziel)
    con.execute("VACUUM")
    con.close()
    shutil.copyfile(tmp, db)
    shutil.rmtree(tmp.parent, ignore_errors=True)
    schreibe_befundcodes(ziel)
    print(f"{db}  ({db.stat().st_size / 1e6:.1f} MB)\n{ziel / 'SCHEMA.md'}\n{ziel / 'BEFUNDCODES.md'}")


if __name__ == "__main__":
    main()
