"""Vorgänge anlegen (Mail/Scan), Dokumente unverändert ablegen, Rechnungen bilden, prüfen, Vorschläge speichern."""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from pathlib import Path

from . import config, db, dokument, eml, pruefungen
from . import stammdaten as sd


def protokoll(rechnung_id, ereignis: str, akteur: str, daten: dict | None = None) -> None:
    db.ausfuehren("INSERT INTO app.protokoll (rechnung_id, ereignis, akteur, daten) VALUES (%s,%s,%s,%s)",
                  (rechnung_id, ereignis, akteur, db.json(daten or {})))


def _ablegen(vorgang_id: uuid.UUID, dateiname: str, inhalt: bytes) -> tuple[str, str]:
    sha = hashlib.sha256(inhalt).hexdigest()
    ziel = config.DOKUMENT_DIR / str(vorgang_id)
    ziel.mkdir(parents=True, exist_ok=True)
    pfad = ziel / f"{sha[:12]}_{Path(dateiname).name}"
    if not pfad.exists():
        pfad.write_bytes(inhalt)
        pfad.chmod(0o444)  # GoBD: Belege werden nicht verändert
    return sha, str(pfad)


def mail_eingang(raw: bytes, quelle: str = "email") -> dict:
    """Mail protokollieren; nur wenn sie Rechnungsdokumente enthält, einen Vorgang anlegen."""
    m = eml.parse(raw)
    anh = [{"dateiname": a.dateiname, "mime": a.mime, "bytes": len(a.inhalt), "rechnungsdokument": a.ist_rechnungsdokument} for a in m.anhaenge]
    bestehend = db.eins("SELECT vorgang_id FROM app.mail_log WHERE message_id=%s", (m.message_id,))
    if bestehend:
        v = bestehend["vorgang_id"]
        return {"message_id": m.message_id, "ist_rechnung": m.ist_rechnung, "anhaenge": anh, "vorgang_id": str(v) if v else None,
                "rechnungen": _rechnung_ids(v) if v else [], "bereits_verarbeitet": True}
    vorgang_id = None
    rechnungen = []
    if m.ist_rechnung:
        vorgang_id = uuid.uuid4()
        db.ausfuehren("INSERT INTO app.vorgang (id, quelle, message_id, eingang, absender, reply_to, betreff, mailtext, raw_sha256) "
                      "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                      (vorgang_id, quelle, m.message_id, m.eingang, m.absender, m.reply_to, m.betreff, m.text[:20000], m.sha256))
        _ablegen(vorgang_id, "original.eml", raw)
        rechnungen = _rechnungen_bilden(vorgang_id, [(a.dateiname, a.inhalt) for a in m.rechnungsanhaenge])
    db.ausfuehren("INSERT INTO app.mail_log (message_id, eingang, absender, absender_domain, reply_to, betreff, ist_rechnung, anhaenge, vorgang_id) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (message_id) DO NOTHING",
                  (m.message_id, m.eingang, m.absender, m.absender_domain, m.reply_to, m.betreff, m.ist_rechnung, db.json(anh), vorgang_id))
    return {"message_id": m.message_id, "ist_rechnung": m.ist_rechnung, "anhaenge": anh,
            "vorgang_id": str(vorgang_id) if vorgang_id else None, "rechnungen": rechnungen, "bereits_verarbeitet": False}


def datei_eingang(dateiname: str, inhalt: bytes, eingang: datetime | None = None, quelle: str = "scan") -> dict:
    """Papierrechnung/Scan oder Datei-Upload ohne Mail."""
    vorgang_id = uuid.uuid4()
    db.ausfuehren("INSERT INTO app.vorgang (id, quelle, eingang, betreff) VALUES (%s,%s,%s,%s)",
                  (vorgang_id, quelle, eingang or datetime.now(timezone.utc), dateiname))
    return {"vorgang_id": str(vorgang_id), "rechnungen": _rechnungen_bilden(vorgang_id, [(dateiname, inhalt)])}


def _rechnung_ids(vorgang_id) -> list[str]:
    return [str(r["id"]) for r in db.alle("SELECT id FROM app.rechnung WHERE vorgang_id=%s ORDER BY erstellt_am", (vorgang_id,))]


def _rechnungen_bilden(vorgang_id: uuid.UUID, dateien: list[tuple[str, bytes]]) -> list[str]:
    xml_teile, pdf_teile = [], []
    for name, inhalt in dateien:
        sha, pfad = _ablegen(vorgang_id, name, inhalt)
        dok_id = uuid.uuid4()
        try:
            a = dokument.analysiere(name, inhalt)
            fehler = None
        except Exception as e:  # unlesbares Dokument: trotzdem ablegen, Agent/Mensch sieht es
            a, fehler = {"format": "unlesbar", "text": "", "seiten": None, "extrakte": []}, str(e)
        fmt = a["format"] or (a["extrakte"][0]["format"] if a["extrakte"] else "unbekannt")
        db.ausfuehren("INSERT INTO app.dokument (id, vorgang_id, dateiname, typ, format, sha256, pfad, seiten, text) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                      (dok_id, vorgang_id, name, name.rsplit(".", 1)[-1].lower(), fmt, sha, pfad, a["seiten"], (a["text"] or "")[:50000]))
        for x in a["extrakte"]:
            x["dokument_id"] = str(dok_id)
            x["dateiname"] = name
            if fehler:
                x["lesefehler"] = fehler
            (xml_teile if x["format"].startswith("xml") else pdf_teile).append(x)

    ids = []
    rest_pdf = list(pdf_teile)
    for x in xml_teile:
        partner = next((p for p in rest_pdf if sd.norm_rnr(p.get("rechnungsnr")) == sd.norm_rnr(x.get("rechnungsnr"))), None)
        if partner is None and len(xml_teile) == 1 and len(rest_pdf) == 1:
            partner = rest_pdf[0]
        if partner:
            rest_pdf.remove(partner)
            _ergaenzen(x, partner)
        ids.append(_rechnung_anlegen(vorgang_id, x, partner))
    for p in rest_pdf:
        ids.append(_rechnung_anlegen(vorgang_id, p, None))
    return ids


def _ergaenzen(xml: dict, pdf: dict) -> None:
    """Felder, die im XML fehlen, aus dem PDF übernehmen (XML bleibt führend)."""
    for feld in ("bic", "bank", "register", "telefon", "steuernummer"):
        if not xml["lieferant"].get(feld) and pdf["lieferant"].get(feld):
            xml["lieferant"][feld] = pdf["lieferant"][feld]
    if xml.get("skonto") and not xml["skonto"].get("bis") and pdf.get("skonto"):
        xml["skonto"]["bis"] = pdf["skonto"].get("bis")
    for feld in ("ersetzt_rechnungsnr", "bezug_rechnungsnr"):
        if not xml.get(feld) and pdf.get(feld):
            xml[feld] = pdf[feld]
    if pdf.get("typ") in ("korrektur", "gutschrift") and xml.get("typ") == "rechnung":
        xml["typ"] = pdf["typ"]


def _rechnung_anlegen(vorgang_id, extrakt: dict, pdf_partner: dict | None) -> str:
    rid = uuid.uuid4()
    extrakt["rnr_norm"] = sd.norm_rnr(extrakt.get("rechnungsnr"))
    if pdf_partner:
        extrakt["pdf_partner"] = pdf_partner
    doks = [extrakt["dokument_id"]] + ([pdf_partner["dokument_id"]] if pdf_partner else [])
    db.ausfuehren("INSERT INTO app.rechnung (id, vorgang_id, dokument_ids, extrakt) VALUES (%s,%s,%s,%s)",
                  (rid, vorgang_id, doks, db.json(extrakt)))
    protokoll(rid, "rechnung_erkannt", "pruefdienst", {"format": extrakt["format"], "rechnungsnr": extrakt.get("rechnungsnr")})
    return str(rid)


# --------------------------------------------------------------------------- Prüfen

def lade_rechnung(rechnung_id: str) -> tuple[dict, dict]:
    r = db.eins("SELECT * FROM app.rechnung WHERE id=%s", (rechnung_id,))
    if not r:
        raise KeyError(f"Rechnung {rechnung_id} unbekannt")
    v = db.eins("SELECT * FROM app.vorgang WHERE id=%s", (r["vorgang_id"],))
    v["absender_domain"] = (v.get("absender") or "").split("@")[-1].strip(" >").lower() if v.get("absender") else ""
    return r, v


def pruefe_rechnung(rechnung_id: str, korrekturen: dict | None = None, akteur: str = "pruefdienst") -> dict:
    r, v = lade_rechnung(rechnung_id)
    extrakt = r["extrakt"]
    if korrekturen:
        extrakt = _wende_korrekturen_an(extrakt, korrekturen)
        db.ausfuehren("UPDATE app.rechnung SET korrekturen=%s WHERE id=%s", (db.json(korrekturen), rechnung_id))
        protokoll(rechnung_id, "extrakt_korrigiert", akteur, korrekturen)
    ergebnis = pruefungen.pruefe(extrakt, v, extrakt.get("pdf_partner"))
    db.ausfuehren("UPDATE app.rechnung SET pruefung=%s WHERE id=%s", (db.json(ergebnis), rechnung_id))
    protokoll(rechnung_id, "regelpruefung", akteur, {"regelversion": ergebnis["regelversion"],
                                                     "befunde": [b["code"] for b in ergebnis["befunde"]],
                                                     "regelvorschlag": ergebnis["regelvorschlag"]["entscheidung"]})
    return ergebnis


def _wende_korrekturen_an(extrakt: dict, korrekturen: dict) -> dict:
    x = dict(extrakt)
    for k, wert in korrekturen.items():
        if k == "lieferant" and isinstance(wert, dict):
            x["lieferant"] = {**x["lieferant"], **wert}
        elif k in x:
            x[k] = wert
    x["rnr_norm"] = sd.norm_rnr(x.get("rechnungsnr"))
    return x


ENTSCHEIDUNGEN = ("freigeben", "klaeren", "ablehnen")


def speichere_vorschlag(rechnung_id: str, entscheidung: str, begruendungen: list[dict], zusammenfassung: str | None,
                        quelle: str, srw_job_id: str | None = None) -> dict:
    if entscheidung not in ENTSCHEIDUNGEN:
        raise ValueError(f"entscheidung muss eine von {ENTSCHEIDUNGEN} sein")
    if entscheidung != "freigeben" and not begruendungen:
        raise ValueError("Für klären/ablehnen ist mindestens eine Begründung nötig")
    for b in begruendungen:
        if not b.get("text"):
            raise ValueError("Jede Begründung braucht einen Text")
    r = db.eins("SELECT pruefung FROM app.rechnung WHERE id=%s", (rechnung_id,))
    if not r or not r["pruefung"]:
        raise ValueError("Rechnung wurde noch nicht geprüft (pruefe_rechnung zuerst aufrufen)")
    p = r["pruefung"]
    vid = uuid.uuid4()
    db.ausfuehren("INSERT INTO app.vorschlag (id, rechnung_id, quelle, entscheidung, begruendungen, zusammenfassung, freigabe, kontierung, skonto, regelversion, srw_job_id) "
                  "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                  (vid, rechnung_id, quelle, entscheidung, db.json(begruendungen), zusammenfassung,
                   db.json(p["freigabe"]), db.json(p["kontierung"]), db.json(p["skonto"]), p["regelversion"], srw_job_id))
    protokoll(rechnung_id, "vorschlag", quelle, {"vorschlag_id": str(vid), "entscheidung": entscheidung})
    return {"vorschlag_id": str(vid), "entscheidung": entscheidung, "freigabe": p["freigabe"]}


def regelpruefung_vorgang(vorgang_id: str) -> list[dict]:
    """Baseline ohne Agent: alle Rechnungen prüfen und Regelvorschlag speichern."""
    out = []
    for rid in _rechnung_ids(vorgang_id):
        e = pruefe_rechnung(rid)
        rv = e["regelvorschlag"]
        out.append({"rechnung_id": rid, **speichere_vorschlag(rid, rv["entscheidung"], rv["begruendungen"], None, "regeln")})
    return out


# --------------------------------------------------------------------------- Entscheidungs-Links

def link_token(rechnung_id: str, aktion: str) -> str:
    return hmac.new(config.LINK_SECRET.encode(), f"{rechnung_id}:{aktion}".encode(), hashlib.sha256).hexdigest()[:32]


def entscheidung_speichern(rechnung_id: str, aktion: str, token: str, kommentar: str | None = None) -> dict:
    if not hmac.compare_digest(link_token(rechnung_id, aktion), token or ""):
        raise PermissionError("Ungültiger Link")
    v = db.eins("SELECT * FROM app.vorschlag WHERE rechnung_id=%s ORDER BY erstellt_am DESC LIMIT 1", (rechnung_id,))
    if not v:
        raise KeyError("Kein Vorschlag zu dieser Rechnung")
    if aktion == "vorschlag_falsch" and not (kommentar or "").strip():
        return {"formular": True, "aktion": aktion, "vorschlag": v["entscheidung"]}
    person = (v["freigabe"] or {}).get("name")
    eid = uuid.uuid4()
    db.ausfuehren("INSERT INTO app.entscheidung (id, rechnung_id, vorschlag_id, aktion, person, kommentar) VALUES (%s,%s,%s,%s,%s,%s)",
                  (eid, rechnung_id, v["id"], aktion, person, kommentar))
    protokoll(rechnung_id, "entscheidung", person or "unbekannt", {"aktion": aktion, "kommentar": kommentar, "vorschlag": v["entscheidung"]})
    vg = db.eins("SELECT v.srw_job_id FROM app.vorgang v JOIN app.rechnung r ON r.vorgang_id=v.id WHERE r.id=%s", (rechnung_id,))
    return {"entscheidung_id": str(eid), "aktion": aktion, "person": person, "vorschlag": v["entscheidung"],
            "uebereinstimmung": aktion == v["entscheidung"], "srw_job_id": (vg or {}).get("srw_job_id") or v.get("srw_job_id")}
