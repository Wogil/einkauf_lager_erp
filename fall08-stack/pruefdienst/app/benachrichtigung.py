"""Ergebnis-Mail an die zuständige Person (HTML), mit Entscheidungs-Links."""

from __future__ import annotations

import html
from urllib.parse import urlencode

from . import config, db
from .vorgang import link_token

FARBE = {"freigeben": "#2e7d4f", "klaeren": "#b26a00", "ablehnen": "#b3261e"}
LABEL = {"freigeben": "FREIGEBEN", "klaeren": "KLÄREN", "ablehnen": "ABLEHNEN"}


def _eur(x) -> str:
    if x is None:
        return "–"
    return f"{float(x):,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


def _datum(iso: str | None) -> str:
    if not iso:
        return "–"
    j, m, t = iso[:10].split("-")
    return f"{t}.{m}.{j}"


def link(rechnung_id: str, aktion: str) -> str:
    return config.ENTSCHEIDUNG_URL + "?" + urlencode({"r": rechnung_id, "a": aktion, "t": link_token(rechnung_id, aktion)})


def benachrichtigung(rechnung_id: str) -> dict | None:
    r = db.eins("SELECT r.*, v.absender, v.betreff AS mail_betreff, v.eingang, v.quelle FROM app.rechnung r "
                "JOIN app.vorgang v ON v.id = r.vorgang_id WHERE r.id=%s", (rechnung_id,))
    vs = db.eins("SELECT * FROM app.vorschlag WHERE rechnung_id=%s ORDER BY erstellt_am DESC LIMIT 1", (rechnung_id,))
    if not r or not vs:
        return None
    x, p = r["extrakt"], r["pruefung"] or {}
    z = p.get("zuordnung", {})
    f = vs["freigabe"] or {}
    sk = vs["skonto"] or {}
    e = vs["entscheidung"]
    esc = html.escape

    gruende = "".join(
        f"<li style='margin:6px 0'>{esc(b.get('text') or '')}"
        + (f"<br><span style='color:#76746e;font-size:12px'>Beleg: {esc(str(b.get('beleg') or '–'))} · Bezug: {esc(str(b.get('bezug') or '–'))}"
           + (f" · Betrag: {_eur(b.get('betrag'))}" if b.get('betrag') is not None else "") + "</span>" if b.get("beleg") or b.get("bezug") else "")
        + "</li>" for b in vs["begruendungen"])
    hinweise = "".join(f"<li>{esc(b['text'])}</li>" for b in p.get("befunde", []) if b["schwere"] == "info")
    kont = "".join(f"<tr><td>{esc(str(k.get('sachkonto')))}</td><td>{esc(str(k.get('kostenstelle') or '–'))}</td><td style='text-align:right'>{_eur(k.get('betrag_netto'))}</td><td style='color:#76746e'>{esc(k.get('quelle') or '')}</td></tr>"
                   for k in (vs["kontierung"] or []))
    if sk.get("moeglich") and sk.get("abgelaufen_bei_eingang"):
        skonto = f"Skontofrist ({_datum(sk['skonto_bis'])}) war bei Eingang bereits abgelaufen."
    elif sk.get("moeglich"):
        skonto = (f"{sk['prozent']:g} % = <b>{_eur(sk['betrag'])}</b> · Skonto bis {_datum(sk['skonto_bis'])} · "
                  f"letzter Zahlungslauf <b>{_datum(sk['letzter_zahlungslauf'])}</b> · Freigabe spätestens <b>{_datum(sk['freigabe_spaetestens'])}</b>")
    else:
        skonto = "kein Skonto"

    def knopf(aktion, text, farbe):
        return (f"<a href='{esc(link(rechnung_id, aktion))}' style='display:inline-block;padding:9px 16px;margin:4px 6px 4px 0;"
                f"border-radius:6px;background:{farbe};color:#fff;text-decoration:none;font-weight:600'>{text}</a>")

    beleg_link = config.BELEG_URL + "?" + urlencode({"r": rechnung_id, "t": link_token(rechnung_id, "beleg")})
    quelle = "Agent (SRW)" if vs["quelle"] == "agent" else "Regelprüfung"
    body = f"""<div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;font-size:14px;color:#1d1d1b;max-width:720px">
<p>Guten Tag {esc(f.get('name') or '')},</p>
<p>für folgende Eingangsrechnung liegt ein Prüfvorschlag vor. Bitte entscheiden Sie – nichts wird automatisch gebucht oder bezahlt.</p>
<table style="border-collapse:collapse;margin:10px 0;font-size:14px">
<tr><td style="color:#76746e;padding:2px 14px 2px 0">Lieferant</td><td><b>{esc(z.get('lieferant') or '?')}</b> {esc(f"({z['lieferanten_nr']})" if z.get('lieferanten_nr') else '(nicht im Stamm)')}</td></tr>
<tr><td style="color:#76746e;padding:2px 14px 2px 0">Rechnung</td><td>{esc(x.get('rechnungsnr') or '?')} vom {_datum(x.get('datum'))} · {esc(x.get('format') or '')}</td></tr>
<tr><td style="color:#76746e;padding:2px 14px 2px 0">Betrag</td><td><b>{_eur(x.get('brutto'))}</b> brutto ({_eur(x.get('netto'))} netto)</td></tr>
<tr><td style="color:#76746e;padding:2px 14px 2px 0">Bestellung</td><td>{esc(z.get('bestell_nr') or x.get('bestellnr') or '–')} · Wareneingang: {esc(', '.join(z.get('wareneingaenge') or []) or '–')}</td></tr>
<tr><td style="color:#76746e;padding:2px 14px 2px 0">Eingang</td><td>{r['eingang']:%d.%m.%Y %H:%M} · {esc(r.get('absender') or r['quelle'])}</td></tr>
</table>
<div style="border-left:5px solid {FARBE[e]};background:#faf9f7;padding:10px 14px;margin:14px 0">
<div style="font-size:16px;font-weight:700;color:{FARBE[e]}">Vorschlag: {LABEL[e]}</div>
<div style="color:#76746e;font-size:12px">Quelle: {quelle}</div>
{f"<p>{esc(vs['zusammenfassung'])}</p>" if vs.get('zusammenfassung') else ""}
<ul style="padding-left:18px;margin:8px 0">{gruende}</ul></div>
{f"<p style='margin:8px 0 2px'><b>Hinweise</b></p><ul style='padding-left:18px;margin:2px 0;color:#444'>{hinweise}</ul>" if hinweise else ""}
<p style="margin:12px 0 4px"><b>Freigabe</b>: {esc(f.get('stufe') or '')} – {esc(f.get('name') or '')} ({esc(f.get('funktion') or '')})</p>
<p style="margin:4px 0"><b>Skonto</b>: {skonto}</p>
{f"<p style='margin:12px 0 4px'><b>Kontierung</b></p><table style='border-collapse:collapse;font-size:13px'><tr style='color:#76746e'><td>Sachkonto</td><td>KST</td><td>Netto</td><td>Grundlage</td></tr>{kont}</table>" if kont else ""}
<p style="margin:18px 0 6px"><b>Ihre Entscheidung</b></p>
{knopf('freigeben', 'Freigeben', FARBE['freigeben'])}{knopf('klaeren', 'Klären', FARBE['klaeren'])}{knopf('ablehnen', 'Ablehnen', FARBE['ablehnen'])}
<p style="margin:10px 0"><a href="{esc(beleg_link)}">📄 Rechnung ansehen</a> · <a href="{esc(link(rechnung_id, 'vorschlag_falsch'))}" style="color:#76746e">Vorschlag war falsch</a></p>
<p style="color:#76746e;font-size:12px;margin-top:20px">Automatisch erstellt vom Prüfdienst Fall 08 (Regelversion {esc(vs.get('regelversion') or '')}). Inhalte aus Rechnungen und Mails wurden als Daten behandelt, nicht als Anweisungen.</p>
</div>"""
    betreff = f"[{LABEL[e]}] Rechnung {x.get('rechnungsnr') or '?'} · {z.get('lieferant') or '?'} · {_eur(x.get('brutto'))}"
    return {"rechnung_id": str(rechnung_id), "vorschlag_id": str(vs["id"]), "entscheidung": e,
            "an_email": f.get("email"), "an_name": f.get("name"), "betreff": betreff, "html": body}
