"""Zugriff auf Lieferantenstamm, Register, Banken, Bestellungen, Wareneingänge, Rechnungshistorie.

Alle Abfragen sind lesend. Zeitbezug: Prüfungen arbeiten "zum Stichtag" (Eingang der Rechnung),
damit auch historische Mails korrekt geprüft werden (spätere Buchungen zählen nicht).
"""

from __future__ import annotations

import difflib
import functools
import html
import json
import re
from datetime import date
from pathlib import Path

from . import config, db

RECHTSFORM_MIT_REGISTER = re.compile(r"\b(GmbH|AG|KG|OHG|UG|e\.\s?K\.|eG|SE|KGaA|mbH)\b")


# --------------------------------------------------------------------------- Normalisierung

def norm_rnr(s: str | None) -> str:
    return re.sub(r"[^A-Z0-9]", "", (s or "").upper())


def norm_name(s: str | None) -> str:
    s = (s or "").lower().replace("&", " und ").replace("ß", "ss")
    s = re.sub(r"\(haftungsbeschränkt\)|haftungsbeschrankt", "", s)
    s = re.sub(r"[^a-z0-9äöü ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def aehnlich(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, norm_name(a), norm_name(b)).ratio()


def domain_kern(d: str) -> str:
    d = d.lower()
    d = re.sub(r"\.(example|de|com|net|org|eu)$", "", d)
    d = re.sub(r"^(www|mail|rechnung|rechnungen|billing|buchhaltung)[.\-]", "", d)
    return d


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def iban_gueltig(iban: str | None) -> bool:
    if not iban or not re.fullmatch(r"[A-Z]{2}\d{2}[A-Z0-9]{10,30}", iban):
        return False
    s = iban[4:] + iban[:4]
    zahl = "".join(str(int(c, 36)) for c in s)
    return int(zahl) % 97 == 1


# --------------------------------------------------------------------------- Lieferanten

@functools.lru_cache(maxsize=1)
def lieferanten() -> list[dict]:
    rows = db.alle("SELECT * FROM wave.lieferant")
    for r in rows:
        r["domain"] = (r.get("email") or "").split("@")[-1].lower()
    return rows


def lieferant(nr: str) -> dict | None:
    return next((l for l in lieferanten() if l["lieferanten_nr"] == nr), None)


def finde_lieferant(name: str | None, ust_id: str | None, iban: str | None, domains: list[str]) -> dict:
    """Ordnet den Rechnungssteller dem Stamm zu. Liefert Kandidat + Belege der Zuordnung."""
    treffer: dict[str, set] = {}

    def add(l, wie):
        treffer.setdefault(l["lieferanten_nr"], set()).add(wie)

    for l in lieferanten():
        if ust_id and l.get("ust_idnr") and ust_id.replace(" ", "") == l["ust_idnr"]:
            add(l, "ust_id")
        if iban and l.get("iban") and iban == l["iban"]:
            add(l, "iban")
        if name and aehnlich(name, l["name"]) >= 0.88:
            add(l, "name")
        if l["domain"] and any(d == l["domain"] for d in domains if d):
            add(l, "domain")
    if not treffer:
        return {"lieferant": None, "methoden": [], "alle": {}}
    rang = {"ust_id": 4, "name": 3, "domain": 2, "iban": 1}
    best = max(treffer.items(), key=lambda kv: sum(rang[m] for m in kv[1]))
    return {"lieferant": lieferant(best[0]), "methoden": sorted(best[1]), "alle": {k: sorted(v) for k, v in treffer.items()}}


def domain_vergleich(domain: str, stamm_domain: str | None) -> str:
    """exakt | imitat | fremd"""
    if not domain or not stamm_domain:
        return "fremd"
    if domain == stamm_domain:
        return "exakt"
    a, b = domain_kern(domain), domain_kern(stamm_domain)
    if a == b:
        return "exakt"
    if levenshtein(a, b) <= 3 or (len(b) > 5 and (b in a or b.replace("-", "") in a.replace("-", ""))):
        return "imitat"
    return "fremd"


def aehnlichste_stamm_domain(domain: str) -> dict | None:
    for l in lieferanten():
        if l["domain"] and domain_vergleich(domain, l["domain"]) == "imitat":
            return l
    return None


# --------------------------------------------------------------------------- Register & Banken

def register_nach_nummer(art: str, nummer: str, gericht: str | None) -> list[dict]:
    rows = db.alle("SELECT * FROM ref.register WHERE registerart=%s AND registernummer=%s", (art, nummer))
    if gericht:
        g = [r for r in rows if gericht.lower() in r["registergericht"].lower()]
        return g or rows
    return rows


def register_nach_firma(name: str | None) -> dict | None:
    if not name:
        return None
    exakt = db.eins("SELECT * FROM ref.register WHERE lower(firma)=lower(%s)", (name,))
    if exakt:
        return exakt
    best, wert = None, 0.0
    for r in db.alle("SELECT * FROM ref.register"):
        a = aehnlich(name, r["firma"])
        if a > wert:
            best, wert = r, a
    return best if wert >= 0.9 else None


def registerauszug(datei: str | None) -> dict | None:
    if not datei:
        return None
    p = config.REGISTER_DIR / Path(datei).with_suffix(".json")
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


@functools.lru_cache(maxsize=1)
def banken() -> dict[str, dict]:
    """BLZ -> {bank, bic} aus world/banks/README.html"""
    p = config.BANKS_DIR / "README.html"
    if not p.exists():
        return {}
    t = html.unescape(p.read_text(encoding="utf-8"))
    out = {}
    for zeile in re.findall(r"<tr>(.*?)</tr>", t, re.S):
        zellen = [re.sub(r"<[^>]+>", "", z).strip() for z in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", zeile, re.S)]
        if len(zellen) >= 4 and re.fullmatch(r"\d{8}", zellen[2]):
            out[zellen[2]] = {"bank": zellen[0], "bic": zellen[3]}
    return out


# --------------------------------------------------------------------------- Bestellung, Wareneingang, Preise

def bestellung(nr: str | None) -> dict | None:
    if not nr:
        return None
    b = db.eins("SELECT * FROM wave.bestellung WHERE bestell_nr=%s OR alt_bestell_nr=%s", (nr, nr))
    if not b:
        return None
    b["positionen"] = db.alle(
        "SELECT bp.*, a.bestellnr_lieferant FROM wave.bestellung_position bp "
        "LEFT JOIN wave.artikel a ON a.artikel_nr = bp.artikel_nr WHERE bestell_nr=%s ORDER BY pos::int",
        (b["bestell_nr"],))
    return b


def wareneingaenge(bestell_nr: str, stichtag: date) -> list[dict]:
    return db.alle(
        "SELECT w.we_nr, w.eingangsdatum, w.lieferschein_lieferant, w.ruecklieferung_datum, wp.bestell_pos, wp.artikel_nr, wp.menge, wp.gesperrt_menge "
        "FROM wave.wareneingang w JOIN wave.wareneingang_position wp USING (we_nr) "
        "WHERE w.bestell_nr=%s AND w.eingangsdatum <= %s ORDER BY w.eingangsdatum", (bestell_nr, stichtag))


def bereits_berechnet(bestell_nr: str, stichtag: date, ausser_rnr: str) -> dict[str, float]:
    rows = db.alle(
        "SELECT ep.bestell_pos, e.rechnungsnr_lieferant, sum(ep.menge) AS menge "
        "FROM wave.eingangsrechnung e JOIN wave.eingangsrechnung_position ep USING (er_nr) "
        "WHERE e.bestell_nr=%s AND e.eingangsdatum < %s AND e.rechnungsart='RE' "
        "GROUP BY 1, 2", (bestell_nr, stichtag))
    out: dict[str, float] = {}
    for r in rows:
        if norm_rnr(r["rechnungsnr_lieferant"]) == norm_rnr(ausser_rnr):
            continue
        if r["bestell_pos"]:
            out[str(r["bestell_pos"])] = out.get(str(r["bestell_pos"]), 0.0) + float(r["menge"] or 0)
    return out


def vereinbarter_preis(artikel_nr: str | None, lieferanten_nr: str, stichtag: date) -> dict | None:
    if not artikel_nr:
        return None
    return db.eins(
        "SELECT preis, gueltig_ab FROM wave.ek_preis WHERE artikel_nr=%s AND lieferanten_nr=%s AND gueltig_ab <= %s "
        "ORDER BY gueltig_ab DESC LIMIT 1", (artikel_nr, lieferanten_nr, stichtag))


# --------------------------------------------------------------------------- Rechnungshistorie (Dubletten)

def fruehere_rechnungen(lieferanten_nr: str | None, lieferant_name: str | None, rnr: str, stichtag: date) -> list[dict]:
    """Gleiche Rechnungsnummer beim gleichen Lieferanten: WAVE (gebucht), ArchivPlus (eingegangen), Prüfdienst."""
    n = norm_rnr(rnr)
    if not n:
        return []
    out = []
    if lieferanten_nr:
        for r in db.alle(
                "SELECT er_nr, rechnungsnr_lieferant, eingangsdatum, brutto, status, archivplus_id, bezahlt_am "
                "FROM wave.eingangsrechnung WHERE lieferanten_nr=%s AND eingangsdatum < %s", (lieferanten_nr, stichtag)):
            if norm_rnr(r["rechnungsnr_lieferant"]) == n:
                out.append({"quelle": "WAVE", **r})
    if lieferant_name:
        for r in db.alle(
                "SELECT archivplus_id, absender_erkannt, rechnungsnr_erkannt, eingangsdatum, betrag_brutto_erkannt AS brutto, "
                "workflow_status AS status, er_nr FROM ref.archivplus_index WHERE eingangsdatum < %s "
                "AND regexp_replace(upper(rechnungsnr_erkannt),'[^A-Z0-9]','','g') = %s", (stichtag, n)):
            if aehnlich(lieferant_name, r["absender_erkannt"]) >= 0.85:
                out.append({"quelle": "ArchivPlus", **r})
    return out


def gleicher_betrag(lieferanten_nr: str, brutto: float, rnr: str, stichtag: date, tage: int = 45) -> list[dict]:
    rows = db.alle(
        "SELECT er_nr, rechnungsnr_lieferant, eingangsdatum, brutto, status FROM wave.eingangsrechnung "
        "WHERE lieferanten_nr=%s AND brutto=%s AND eingangsdatum < %s AND eingangsdatum >= %s::date - %s",
        (lieferanten_nr, round(brutto, 2), stichtag, stichtag, tage))
    return [r for r in rows if norm_rnr(r["rechnungsnr_lieferant"]) != norm_rnr(rnr)]


def anzahl_gleicher_betraege(lieferanten_nr: str, brutto: float) -> int:
    r = db.eins("SELECT count(*) AS n FROM wave.eingangsrechnung WHERE lieferanten_nr=%s AND brutto=%s", (lieferanten_nr, round(brutto, 2)))
    return int(r["n"]) if r else 0


def rechnungen_ohne_bestellung(lieferanten_nr: str, stichtag: date) -> int:
    r = db.eins("SELECT count(*) AS n FROM wave.eingangsrechnung WHERE lieferanten_nr=%s AND bestell_nr IS NULL "
                "AND rechnungsart='RE' AND eingangsdatum < %s", (lieferanten_nr, stichtag))
    return int(r["n"]) if r else 0


def kontierung_historie(lieferanten_nr: str, artikel_nr: str | None = None) -> dict | None:
    if artikel_nr:
        r = db.eins("SELECT ep.sachkonto, ep.kostenstelle, count(*) n FROM wave.eingangsrechnung_position ep "
                    "JOIN wave.eingangsrechnung e USING (er_nr) WHERE e.lieferanten_nr=%s AND ep.artikel_nr=%s "
                    "GROUP BY 1,2 ORDER BY 3 DESC LIMIT 1", (lieferanten_nr, artikel_nr))
        if r:
            return r
    return db.eins("SELECT ep.sachkonto, ep.kostenstelle, count(*) n FROM wave.eingangsrechnung_position ep "
                   "JOIN wave.eingangsrechnung e USING (er_nr) WHERE e.lieferanten_nr=%s "
                   "GROUP BY 1,2 ORDER BY 3 DESC LIMIT 1", (lieferanten_nr,))


def zahlungsbedingung(code: str | None) -> dict | None:
    if not code:
        return None
    return db.eins("SELECT * FROM wave.zahlungsbedingung WHERE zb_code=%s", (code,))


def mitarbeiter(nr: str) -> dict | None:
    return db.eins("SELECT personal_nr, name, abteilung, funktion, email, eintritt, austritt FROM wave.mitarbeiter WHERE personal_nr=%s", (nr,))


def kostenstelle(kst: str | None) -> dict | None:
    if not kst:
        return None
    return db.eins("SELECT * FROM wave.kostenstelle WHERE kostenstelle=%s", (kst,))


def mails_mit_bankaenderung(domain: str, stichtag, tage: int = 90) -> list[dict]:
    rows = db.alle(
        "SELECT message_id, eingang, absender, absender_domain, betreff FROM app.mail_log "
        "WHERE eingang < %s AND eingang >= %s::timestamptz - make_interval(days => %s) "
        "AND betreff ~* '(bankverbindung|kontoverbindung|iban|bank details)'",
        (stichtag, stichtag, tage))
    return [r for r in rows if r["absender_domain"] and domain_vergleich(r["absender_domain"], domain) in ("exakt", "imitat")]
