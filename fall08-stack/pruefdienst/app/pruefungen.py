"""Die festen Prüfregeln (deterministisch, reproduzierbar).

`pruefe(rechnung, vorgang)` liefert:
  - zuordnung   (Lieferant, Bestellung, Wareneingänge)
  - befunde     (Liste mit Code, Schwere, Text, Beleg, Bezug, Betrag)
  - kontierung, freigabe, skonto
  - regelvorschlag (Baseline ohne LLM)
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from . import config, regeln
from . import stammdaten as sd


def _befund(code: str, text: str, beleg: str | None = None, bezug: str | None = None,
            betrag: float | None = None, **daten) -> dict:
    schwere, empfehlung, titel = regeln.REGELN[code]
    return {"code": code, "schwere": schwere, "empfehlung": empfehlung, "titel": titel, "text": text,
            "beleg": beleg, "bezug": bezug, "betrag": round(betrag, 2) if betrag is not None else None,
            "daten": daten or None}


def _d(s: str | None) -> date | None:
    return date.fromisoformat(s) if s else None


def _eur(x: float | None) -> str:
    if x is None:
        return "–"
    return f"{x:,.2f} €".replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------------- Hauptfunktion

def pruefe(extrakt: dict, vorgang: dict, pdf_extrakt: dict | None = None) -> dict:
    """extrakt: führender Extrakt (XML, sonst PDF). pdf_extrakt: PDF-Teil einer ZUGFeRD-Rechnung."""
    befunde: list[dict] = []
    stichtag: date = vorgang["eingang"].date() if isinstance(vorgang["eingang"], datetime) else vorgang["eingang"]
    beleg = f"Rechnung {extrakt.get('rechnungsnr') or '?'}"
    L = extrakt["lieferant"]
    mail_domain = (vorgang.get("absender_domain") or "").lower()
    xml_domain = (L.get("email") or "").split("@")[-1].lower() if L.get("email") else ""

    # ---------------------------------------------------------------- Lieferant zuordnen
    z = sd.finde_lieferant(L.get("name"), L.get("ust_id"), L.get("iban"), [mail_domain, xml_domain])
    lief = z["lieferant"]
    zuordnung = {"lieferanten_nr": lief["lieferanten_nr"] if lief else None,
                 "lieferant": lief["name"] if lief else L.get("name"),
                 "zuordnung_ueber": z["methoden"]}

    # IBAN gehört zu anderem Lieferanten?
    if lief and L.get("iban"):
        fremd = [nr for nr, wie in z["alle"].items() if nr != lief["lieferanten_nr"] and "iban" in wie]
        if fremd:
            andere = sd.lieferant(fremd[0])
            befunde.append(_befund("IBAN_ANDERER_LIEFERANT",
                                   f"IBAN {L['iban']} ist im Stamm bei {andere['name']} ({andere['lieferanten_nr']}) hinterlegt.",
                                   beleg, f"Lieferantenstamm {andere['lieferanten_nr']}"))

    # Registerprüfung
    reg_rechnung = L.get("register")
    reg_eintrag = None
    if lief:
        reg_eintrag = sd.register_nach_firma(lief["name"])
    elif L.get("name"):
        reg_eintrag = sd.register_nach_firma(L["name"])
        if not reg_eintrag and reg_rechnung:
            treffer = sd.register_nach_nummer(reg_rechnung["art"], reg_rechnung["nummer"], reg_rechnung.get("gericht"))
            reg_eintrag = next((t for t in treffer if sd.aehnlich(t["firma"], L["name"]) >= 0.8), None)

    if not lief:
        if reg_eintrag:
            befunde.append(_befund("LIEFERANT_NEU",
                                   f"„{L.get('name')}“ ist nicht im Lieferantenstamm, aber im Handelsregister eingetragen "
                                   f"({reg_eintrag['registergericht']} {reg_eintrag['registerart']} {reg_eintrag['registernummer']}). "
                                   "Prüfliste Punkt 3: Einkauf fragen.", beleg, "Lieferantenstamm WAVE", extrakt.get("brutto")))
        else:
            befunde.append(_befund("LIEFERANT_UNBEKANNT",
                                   f"„{L.get('name')}“ ist weder im Lieferantenstamm noch im Handelsregister zu finden"
                                   + (" – die Registerangabe auf der Rechnung existiert nicht." if reg_rechnung else " – die Rechnung nennt auch kein Register."),
                                   beleg, "Lieferantenstamm WAVE, Handelsregister", extrakt.get("brutto")))
    if reg_eintrag and reg_eintrag.get("status", "").startswith("gelöscht"):
        befunde.append(_befund("LIEFERANT_GELOESCHT", f"{reg_eintrag['firma']}: {reg_eintrag['status']}.", beleg,
                               f"Handelsregister {reg_eintrag['registerart']} {reg_eintrag['registernummer']}"))
    if reg_rechnung and reg_eintrag:
        if (reg_rechnung["art"], reg_rechnung["nummer"]) != (reg_eintrag["registerart"], reg_eintrag["registernummer"]):
            befunde.append(_befund("REGISTER_ABWEICHUNG",
                                   f"Rechnung nennt {reg_rechnung['art']} {reg_rechnung['nummer']} ({reg_rechnung.get('gericht')}), "
                                   f"im Register steht {reg_eintrag['registerart']} {reg_eintrag['registernummer']} ({reg_eintrag['registergericht']}).",
                                   beleg, "Handelsregister"))
    if not reg_rechnung and extrakt["format"].startswith("pdf") and sd.RECHTSFORM_MIT_REGISTER.search(L.get("name") or "") and not lief:
        befunde.append(_befund("REGISTERANGABE_FEHLT", f"„{L.get('name')}“ nennt kein Registergericht/keine Registernummer.", beleg))

    # Bankverbindung
    iban = L.get("iban")
    if iban:
        if not sd.iban_gueltig(iban):
            befunde.append(_befund("IBAN_UNGUELTIG", f"IBAN {iban} hat eine ungültige Prüfziffer.", beleg))
        if lief and lief.get("iban") and iban != lief["iban"]:
            befunde.append(_befund("IBAN_ABWEICHUNG",
                                   f"IBAN auf der Rechnung {iban}, im Lieferantenstamm {lief['iban']}. "
                                   f"Nur nach Rückruf über die Stamm-Rufnummer {lief.get('telefon')} ändern – nie über Kontaktdaten aus Rechnung oder Mail.",
                                   beleg, f"Lieferantenstamm {lief['lieferanten_nr']}", extrakt.get("brutto"),
                                   iban_rechnung=iban, iban_stamm=lief["iban"], rueckruf=lief.get("telefon")))
        if iban.startswith("DE") and len(iban) >= 12:
            blz = iban[4:12]
            bank = sd.banken().get(blz)
            bic = L.get("bic")
            if bank and bic and bic != bank["bic"]:
                befunde.append(_befund("BANK_BLZ_WIDERSPRUCH", f"BLZ {blz} gehört zu {bank['bank']} ({bank['bic']}), Rechnung nennt BIC {bic}.", beleg))

    # Absender-Domain der Mail
    if vorgang.get("quelle") == "email" and mail_domain:
        if lief:
            v = sd.domain_vergleich(mail_domain, lief["domain"])
            if v == "imitat":
                befunde.append(_befund("ABSENDER_DOMAIN_IMITAT",
                                       f"Mail kam von „{mail_domain}“, der Lieferant nutzt „{lief['domain']}“.",
                                       f"Mail {vorgang.get('message_id')}", f"Lieferantenstamm {lief['lieferanten_nr']}"))
            elif v == "fremd":
                befunde.append(_befund("ABSENDER_DOMAIN_FREMD",
                                       f"Mail kam von „{mail_domain}“, im Stamm ist „{lief['domain']}“ hinterlegt.",
                                       f"Mail {vorgang.get('message_id')}", f"Lieferantenstamm {lief['lieferanten_nr']}"))
        else:
            imitiert = sd.aehnlichste_stamm_domain(mail_domain)
            if imitiert:
                befunde.append(_befund("ABSENDER_DOMAIN_IMITAT",
                                       f"Mail-Domain „{mail_domain}“ ähnelt „{imitiert['domain']}“ ({imitiert['name']}).",
                                       f"Mail {vorgang.get('message_id')}", f"Lieferantenstamm {imitiert['lieferanten_nr']}"))
        reply = vorgang.get("reply_to")
        if reply:
            rd = reply.split("@")[-1].strip(" >").lower()
            if rd and rd != mail_domain:
                befunde.append(_befund("REPLY_TO_ABWEICHEND", f"Antworten gehen an „{reply}“ statt an „{mail_domain}“.", f"Mail {vorgang.get('message_id')}"))
        ziel_domain = lief["domain"] if lief else mail_domain
        frueher = [m for m in sd.mails_mit_bankaenderung(ziel_domain, vorgang["eingang"]) if m["message_id"] != vorgang.get("message_id")]
        if frueher:
            m = frueher[-1]
            sauber = lief and L.get("iban") == lief.get("iban") and sd.domain_vergleich(mail_domain, lief["domain"]) == "exakt"
            befunde.append(_befund("BANKAENDERUNG_MAIL_HINWEIS" if sauber else "BANKAENDERUNG_MAIL_VORHER",
                                   f"Am {m['eingang']:%d.%m.%Y} kam „{m['betreff']}“ von {m['absender_domain']}.",
                                   f"Mail {m['message_id']}"))

    # Anweisungen in Freitexten (Prompt-Injection) – Text wird NICHT befolgt
    for t in extrakt.get("freitexte") or []:
        if re.search(regeln.ANWEISUNG_MUSTER, t, re.I):
            befunde.append(_befund("ANWEISUNG_IM_BELEG",
                                   "Ein Bemerkungsfeld richtet sich an automatische Prüfsysteme. Der Inhalt wurde nicht befolgt "
                                   "und ist ein Manipulationsindiz.", beleg, None, None, auszug=t[:200]))
            break

    # ---------------------------------------------------------------- Formal
    emp = (extrakt.get("empfaenger") or {}).get("name") or ""
    if any(f.lower() in emp.lower() for f in config.FALSCHE_EMPFAENGER):
        befunde.append(_befund("FALSCHER_EMPFAENGER",
                               f"Rechnung ist an „{emp}“ adressiert, richtig wäre „{config.EIGENE_FIRMA}“. Zur Korrektur zurückgeben.",
                               beleg, "Prüfliste Punkt 1, Freigaberichtlinie 3."))
    fehlend = []
    if not extrakt.get("rechnungsnr"):
        fehlend.append("Rechnungsnummer")
    if not extrakt.get("datum"):
        fehlend.append("Rechnungsdatum")
    if not (L.get("ust_id") or L.get("steuernummer")) and extrakt["format"].startswith("pdf"):
        fehlend.append("USt-IdNr. oder Steuernummer")
    if extrakt.get("ust") is None and not extrakt.get("reverse_charge_hinweis"):
        fehlend.append("Steuerbetrag")
    if not extrakt.get("positionen"):
        fehlend.append("Menge und Bezeichnung der Leistung")
    if fehlend and extrakt.get("qualitaet") != "ocr":
        befunde.append(_befund("PFLICHTANGABE_FEHLT", "Es fehlt: " + ", ".join(fehlend) + ". Korrigierte Rechnung anfordern.",
                               beleg, "§ 14 Abs. 4 UStG, Prüfliste Punkt 2"))
    if extrakt.get("qualitaet") == "ocr":
        befunde.append(_befund("LESBARKEIT_UNSICHER", "Papierrechnung/Scan: Werte wurden per Texterkennung gelesen und sollten am Bild bestätigt werden.", beleg))

    # Rechnerisch
    netto, ust, brutto = extrakt.get("netto"), extrakt.get("ust"), extrakt.get("brutto")
    pos = extrakt.get("positionen") or []
    rechen = []
    if pos and netto is not None:
        summe = round(sum(p.get("betrag") or 0 for p in pos), 2)
        if abs(summe - netto) > 0.05:
            text_summe = f"Summe der gelesenen Positionen {_eur(summe)} ≠ Nettobetrag {_eur(netto)}"
            if extrakt["format"].startswith("pdf"):
                # Bei PDF/Scan ist das meist ein Lesefehler (umbrochene Zeilen), kein Rechenfehler des Lieferanten
                befunde.append(_befund("POSITIONEN_UNVOLLSTAENDIG",
                                       text_summe + f" (Differenz {_eur(netto - summe)}). Positionen am Beleg nachlesen.",
                                       beleg, None, round(netto - summe, 2)))
            else:
                rechen.append(text_summe)
    for p in pos:
        if p.get("menge") and p.get("einzelpreis") is not None and p.get("betrag") is not None:
            if abs(round(p["menge"] * p["einzelpreis"], 2) - p["betrag"]) > 0.05:
                rechen.append(f"Pos. {p['pos']}: {p['menge']:g} × {_eur(p['einzelpreis'])} ≠ {_eur(p['betrag'])}")
    if None not in (netto, ust, brutto) and abs(netto + ust - brutto) > 0.02:
        rechen.append(f"Netto {_eur(netto)} + USt {_eur(ust)} ≠ Brutto {_eur(brutto)}")
    if None not in (netto, ust) and extrakt.get("ust_satz"):
        if abs(round(netto * extrakt["ust_satz"] / 100, 2) - ust) > 0.05:
            rechen.append(f"USt {_eur(ust)} ≠ {extrakt['ust_satz']:g} % von {_eur(netto)}")
    if rechen:
        befunde.append(_befund("RECHNERISCH_FALSCH", "; ".join(rechen) + ".", beleg))

    if lief and (lief.get("land") or "DE") != "DE" and not extrakt.get("reverse_charge_hinweis"):
        befunde.append(_befund("REVERSE_CHARGE_HINWEIS_FEHLT", f"Lieferant aus {lief['land']}, kein Hinweis auf Reverse Charge.", beleg, "Prüfliste Punkt 11"))

    # ZUGFeRD: PDF und XML vergleichen
    if pdf_extrakt:
        wid = []
        for feld, label in (("rechnungsnr", "Rechnungsnummer"), ("brutto", "Bruttobetrag")):
            a, b = extrakt.get(feld), pdf_extrakt.get(feld)
            if a is not None and b is not None and (sd.norm_rnr(str(a)) != sd.norm_rnr(str(b)) if feld == "rechnungsnr" else abs(a - b) > 0.01):
                wid.append(f"{label}: XML {a}, PDF {b}")
        a, b = extrakt["lieferant"].get("iban"), pdf_extrakt["lieferant"].get("iban")
        if a and b and a != b:
            wid.append(f"IBAN: XML {a}, PDF {b}")
        if wid:
            befunde.append(_befund("PDF_XML_WIDERSPRUCH", "; ".join(wid) + ".", beleg))
        if pdf_extrakt.get("duplikat_vermerk"):
            befunde.append(_befund("DUPLIKAT_VERMERK", "Das PDF trägt den Vermerk Duplikat/Kopie.", beleg))
    elif extrakt.get("duplikat_vermerk"):
        befunde.append(_befund("DUPLIKAT_VERMERK", "Das Dokument trägt den Vermerk Duplikat/Kopie.", beleg))

    # ---------------------------------------------------------------- Dubletten
    rnr = extrakt.get("rechnungsnr") or ""
    if rnr:
        frueher = sd.fruehere_rechnungen(zuordnung["lieferanten_nr"], zuordnung["lieferant"], rnr, stichtag)
        gueltig = [f for f in frueher if not str(f.get("status") or "").startswith("abgelehnt")]
        if gueltig:
            f = gueltig[0]
            nr = f.get("er_nr") or f.get("archivplus_id")
            befunde.append(_befund("DUBLETTE",
                                   f"Rechnung {rnr} ist bereits am {f['eingangsdatum']:%d.%m.%Y} eingegangen ({f['quelle']} {nr}, Status: {f.get('status')}). Nicht erneut zahlen.",
                                   beleg, f"{f['quelle']} {nr}", brutto, frueher=[{k: str(v) for k, v in x.items()} for x in gueltig[:3]]))
        # Korrektur ersetzt Original?
        ersetzt = extrakt.get("ersetzt_rechnungsnr")
        if not ersetzt:
            m = re.match(r"^(.*?)(?:[-/]?K|/\d|-N)$", rnr)
            if m and m.group(1) and m.group(1) != rnr:
                kandidat = sd.fruehere_rechnungen(zuordnung["lieferanten_nr"], zuordnung["lieferant"], m.group(1), stichtag)
                if kandidat:
                    ersetzt = m.group(1)
        if ersetzt:
            orig = sd.fruehere_rechnungen(zuordnung["lieferanten_nr"], zuordnung["lieferant"], ersetzt, stichtag)
            bezahlt = [o for o in orig if o.get("status") == "bezahlt"]
            if bezahlt:
                befunde.append(_befund("KORREKTUR_ORIGINAL_BEZAHLT",
                                       f"{rnr} ersetzt {ersetzt}, das Original wurde bereits bezahlt ({bezahlt[0]['quelle']} {bezahlt[0].get('er_nr') or bezahlt[0].get('archivplus_id')}). Nur Differenz ausgleichen.",
                                       beleg, f"Rechnung {ersetzt}", brutto))
            else:
                befunde.append(_befund("KORREKTUR_ERSETZT", f"{rnr} ersetzt {ersetzt}" + (f" (Original: {orig[0].get('status')})." if orig else "."), beleg, f"Rechnung {ersetzt}"))
    if zuordnung["lieferanten_nr"] and brutto and not any(b["code"] == "DUBLETTE" for b in befunde):
        gleich = sd.gleicher_betrag(zuordnung["lieferanten_nr"], brutto, rnr, stichtag)
        if gleich and sd.anzahl_gleicher_betraege(zuordnung["lieferanten_nr"], brutto) < 3:
            g = gleich[0]
            befunde.append(_befund("MOEGLICHE_DUBLETTE",
                                   f"Am {g['eingangsdatum']:%d.%m.%Y} wurde bereits {_eur(float(g['brutto']))} mit Rechnung {g['rechnungsnr_lieferant']} berechnet ({g['er_nr']}).",
                                   beleg, f"WAVE {g['er_nr']}", brutto))

    # ---------------------------------------------------------------- Bestellung, Preise, Mengen
    leistung = _d(extrakt.get("leistungsdatum")) or _d(extrakt.get("datum")) or stichtag
    best = sd.bestellung(extrakt.get("bestellnr"))
    zuordnung["bestell_nr"] = best["bestell_nr"] if best else None
    positionsabgleich = []
    if extrakt.get("typ") == "gutschrift":
        bezug = extrakt.get("bezug_rechnungsnr")
        if not bezug or not sd.fruehere_rechnungen(zuordnung["lieferanten_nr"], zuordnung["lieferant"], bezug, stichtag + timedelta(days=1)):
            befunde.append(_befund("GUTSCHRIFT_OHNE_BEZUG", "Gutschrift nennt keine bekannte Ursprungsrechnung. Mit welcher offenen Rechnung verrechnen?", beleg, "Prüfliste Punkt 10", brutto))
    elif not extrakt.get("bestellnr"):
        if lief and (lief.get("zb_code") == "LZ05" or sd.rechnungen_ohne_bestellung(lief["lieferanten_nr"], stichtag) >= 3):
            befunde.append(_befund("WIEDERKEHRENDE_LEISTUNG", f"{lief['name']} rechnet üblicherweise ohne Bestellung ab ({lief.get('warengruppe')}).", beleg))
        else:
            befunde.append(_befund("BESTELLUNG_FEHLT", "Die Rechnung nennt keine Bestellnummer. Freigaberichtlinie: Rückfrage beim Besteller, Freigabe nach Bestätigung.", beleg, None, brutto))
    elif not best:
        befunde.append(_befund("BESTELLUNG_UNBEKANNT", f"Bestellung {extrakt['bestellnr']} gibt es in WAVE nicht.", beleg, f"Bestellung {extrakt['bestellnr']}", brutto))
    else:
        if lief and best["lieferanten_nr"] != lief["lieferanten_nr"]:
            andere = sd.lieferant(best["lieferanten_nr"])
            befunde.append(_befund("BESTELLUNG_ANDERER_LIEFERANT",
                                   f"Bestellung {best['bestell_nr']} ging an {andere['name'] if andere else best['lieferanten_nr']}, nicht an {lief['name']}.",
                                   beleg, f"Bestellung {best['bestell_nr']}", brutto))
        we = sd.wareneingaenge(best["bestell_nr"], stichtag)
        zuordnung["wareneingaenge"] = sorted({w["we_nr"] for w in we})
        geliefert: dict[str, float] = {}
        for w in we:
            geliefert[str(w["bestell_pos"])] = geliefert.get(str(w["bestell_pos"]), 0.0) + float(w["menge"] or 0) - float(w["gesperrt_menge"] or 0)
        berechnet = sd.bereits_berechnet(best["bestell_nr"], stichtag, rnr)
        lief_nr = best["lieferanten_nr"]
        frei = list(best["positionen"])
        preis_diff_summe, preis_details, menge_details, pv_angewendet, guenstiger = 0.0, [], [], [], []
        ohne_bezug = []
        for p in pos:
            bp = _passende_bestellposition(p, frei)
            if bp is None:
                ohne_bezug.append(p)
                continue
            frei.remove(bp)
            bpos = str(bp["pos"])
            pv = sd.vereinbarter_preis(bp["artikel_nr"], lief_nr, leistung)
            bestellpreis = float(bp["preis"])
            pv_preis = float(pv["preis"]) if pv else None
            preis = p.get("einzelpreis")
            eintrag = {"rechnung_pos": p.get("pos"), "bestell_pos": bpos, "artikel_nr": bp["artikel_nr"], "bezeichnung": bp["bezeichnung"],
                       "menge": p.get("menge"), "preis": preis, "bestellpreis": bestellpreis, "vereinbarter_preis": pv_preis,
                       "geliefert": geliefert.get(bpos, 0.0), "bereits_berechnet": berechnet.get(bpos, 0.0)}
            positionsabgleich.append(eintrag)
            if preis is not None:
                ok_werte = [bestellpreis] + ([pv_preis] if pv_preis is not None else [])
                if not any(abs(preis - w) < 0.005 for w in ok_werte):
                    ref = pv_preis if pv_preis is not None else bestellpreis
                    diff = round((preis - ref) * (p.get("menge") or 0), 2)
                    if diff > 0:
                        preis_diff_summe += diff
                        preis_details.append(f"Pos. {p.get('pos')} {bp['bezeichnung']}: {_eur(preis)} statt {_eur(ref)} (+{_eur(diff)})")
                    else:
                        guenstiger.append(f"Pos. {p.get('pos')}: {_eur(preis)} statt {_eur(ref)}")
                elif pv_preis is not None and abs(preis - pv_preis) < 0.005 and abs(preis - bestellpreis) >= 0.005:
                    pv_angewendet.append(f"Pos. {p.get('pos')}: {_eur(preis)} lt. Preisvereinbarung ab {pv['gueltig_ab']:%d.%m.%Y} (Bestellung: {_eur(bestellpreis)})")
            offen = geliefert.get(bpos, 0.0) - berechnet.get(bpos, 0.0)
            if p.get("menge") is not None and p["menge"] - offen > 1e-6:
                zuviel = p["menge"] - max(offen, 0)
                menge_details.append(f"Pos. {p.get('pos')} {bp['bezeichnung']}: berechnet {p['menge']:g}, geliefert {geliefert.get(bpos, 0):g}, "
                                     f"davon schon berechnet {berechnet.get(bpos, 0):g}")
                eintrag["zuviel_betrag"] = round(zuviel * (preis or 0), 2)
        if preis_diff_summe > config.PREIS_TOLERANZ_RECHNUNG:
            befunde.append(_befund("PREIS_ABWEICHUNG", "; ".join(preis_details) + ".", beleg,
                                   f"Bestellung {best['bestell_nr']} / Preisvereinbarung", preis_diff_summe))
        if pv_angewendet:
            befunde.append(_befund("PREISVEREINBARUNG_ANGEWENDET", "; ".join(pv_angewendet) + ".", beleg, f"Preisvereinbarung {lief_nr}"))
        if guenstiger:
            befunde.append(_befund("PREIS_UNTER_REFERENZ", "; ".join(guenstiger) + ".", beleg, f"Bestellung {best['bestell_nr']}"))
        if not we:
            befunde.append(_befund("WARENEINGANG_FEHLT", f"Zu Bestellung {best['bestell_nr']} ist bis {stichtag:%d.%m.%Y} kein Wareneingang gebucht.",
                                   beleg, f"Bestellung {best['bestell_nr']}", netto))
        elif menge_details:
            betrag = sum(e.get("zuviel_betrag", 0) for e in positionsabgleich)
            befunde.append(_befund("MENGE_UEBER_WARENEINGANG", "; ".join(menge_details) + ". Berechnet wird höchstens die gelieferte Menge.",
                                   beleg, "Wareneingang " + ", ".join(zuordnung["wareneingaenge"]), betrag))
        for p in ohne_bezug:
            if re.search(regeln.ZUSCHLAG_WOERTER, p.get("bezeichnung") or "", re.I):
                befunde.append(_befund("ZUSCHLAG_NICHT_VEREINBART",
                                       f"Pos. {p.get('pos')} „{p.get('bezeichnung')}“ über {_eur(p.get('betrag'))} ist nicht bestellt/vereinbart. "
                                       "Freigaberichtlinie: nicht vereinbarte Zuschläge werden nicht anerkannt.",
                                       beleg, f"Bestellung {best['bestell_nr']}", p.get("betrag")))
            else:
                befunde.append(_befund("POSITION_OHNE_BESTELLBEZUG", f"Pos. {p.get('pos')} „{p.get('bezeichnung')}“ ({_eur(p.get('betrag'))}) passt zu keiner Bestellposition.",
                                       beleg, f"Bestellung {best['bestell_nr']}", p.get("betrag")))

    # ---------------------------------------------------------------- Kontierung, Freigabe, Skonto
    kontierung = _kontierung(extrakt, lief, best, positionsabgleich)
    freigabe = _freigabe(brutto, best, lief, kontierung, stichtag)
    skonto = _skonto(extrakt, lief, stichtag, befunde, beleg)

    if lief and best is None and netto and netto > 800 and kontierung and kontierung[0]["sachkonto"] not in ("5100", "5400"):
        befunde.append(_befund("ANLAGEGUT_HINWEIS", "Nicht-Material über 800 € netto – ggf. Anlagegut (Frau Kötter informieren).", beleg, "Kontierungsleitfaden"))

    return {
        "regelversion": config.REGELVERSION,
        "stichtag": stichtag.isoformat(),
        "zuordnung": zuordnung,
        "positionsabgleich": positionsabgleich,
        "befunde": befunde,
        "kontierung": kontierung,
        "freigabe": freigabe,
        "skonto": skonto,
        "regelvorschlag": regelvorschlag(befunde),
    }


def _passende_bestellposition(p: dict, frei: list[dict]) -> dict | None:
    if p.get("bestell_pos"):
        for bp in frei:
            if str(bp["pos"]) == str(p["bestell_pos"]):
                return bp
    if p.get("art_nr_kunde"):
        for bp in frei:
            if bp["artikel_nr"] == p["art_nr_kunde"]:
                return bp
    if p.get("art_nr_lieferant"):
        for bp in frei:
            if bp.get("bestellnr_lieferant") and sd.norm_rnr(bp["bestellnr_lieferant"]) == sd.norm_rnr(p["art_nr_lieferant"]):
                return bp
    best, wert = None, 0.0
    for bp in frei:
        a = sd.aehnlich(p.get("bezeichnung"), bp["bezeichnung"])
        if a > wert:
            best, wert = bp, a
    return best if wert >= 0.85 else None


def _kontierung(extrakt: dict, lief: dict | None, best: dict | None, abgleich: list[dict]) -> list[dict]:
    if not lief:
        return []
    zeilen = []
    if best and best.get("bestellart") in ("Material", "Handelsware") and abgleich:
        konten: dict[tuple, float] = {}
        preise = {str(e["rechnung_pos"]): e for e in abgleich}
        for p in extrakt.get("positionen") or []:
            e = preise.get(str(p.get("pos")))
            h = sd.kontierung_historie(lief["lieferanten_nr"], e["artikel_nr"] if e else None)
            key = (h["sachkonto"], None) if h else ("5100", None)
            konten[key] = konten.get(key, 0.0) + (p.get("betrag") or 0)
        for (konto, kst), betrag in konten.items():
            zeilen.append({"sachkonto": konto, "kostenstelle": kst, "betrag_netto": round(betrag, 2),
                           "quelle": "Material mit Bestellung: Konto lt. bisheriger Buchung des Artikels, keine Kostenstelle"})
        return zeilen
    kst = best.get("kostenstelle") if best else None
    h = sd.kontierung_historie(lief["lieferanten_nr"])
    if h:
        zeilen.append({"sachkonto": h["sachkonto"], "kostenstelle": kst or h["kostenstelle"], "betrag_netto": extrakt.get("netto"),
                       "quelle": f"bisherige Buchungen dieses Lieferanten ({h['n']}×)"})
    elif lief.get("warengruppe") in regeln.LEITFADEN:
        konto, k = regeln.LEITFADEN[lief["warengruppe"]]
        zeilen.append({"sachkonto": konto, "kostenstelle": kst or k, "betrag_netto": extrakt.get("netto"),
                       "quelle": f"Kontierungsleitfaden, Gruppe {lief['warengruppe']}"})
    return zeilen


def _freigabe(brutto: float | None, best: dict | None, lief: dict | None, kontierung: list[dict], stichtag: date) -> dict:
    b = abs(brutto or 0)
    if b <= config.GRENZE_SACHBEARBEITUNG:
        stufe, nr = "Sachbearbeitung Kreditorenbuchhaltung", regeln.SACHBEARBEITUNG
    elif b <= config.GRENZE_ABTEILUNGSLEITUNG:
        abt = None
        if best and best.get("bestellart") in ("Material", "Handelsware"):
            abt = "EK"
        else:
            kst = (best or {}).get("kostenstelle") or (kontierung[0]["kostenstelle"] if kontierung else None)
            k = sd.kostenstelle(kst)
            abt = k["abteilung"] if k and k.get("abteilung") else "FI"
        stufe, nr = f"Abteilungsleitung ({abt})", regeln.ABTEILUNGSLEITUNG.get(abt, "10012")
    else:
        stufe, nr = "Kaufmännische Geschäftsführung", regeln.GF_KAUFMAENNISCH[-1][0]
        for pnr, von, bis in regeln.GF_KAUFMAENNISCH:
            if (von is None or stichtag >= date.fromisoformat(von)) and (bis is None or stichtag <= date.fromisoformat(bis)):
                nr = pnr
    m = sd.mitarbeiter(nr) or {}
    return {"stufe": stufe, "personal_nr": nr, "name": m.get("name"), "email": m.get("email"), "funktion": m.get("funktion"),
            "grundlage": "Freigaberichtlinie 2024, Ziffer 2 (Bruttobetrag)", "frist_arbeitstage": 3}


def _skonto(extrakt: dict, lief: dict | None, stichtag: date, befunde: list[dict], beleg: str) -> dict | None:
    zb = sd.zahlungsbedingung(lief.get("zb_code")) if lief else None
    rech = extrakt.get("skonto")
    rdatum = _d(extrakt.get("datum")) or stichtag
    tage = pct = None
    quelle = None
    if rech and rech.get("tage"):
        tage, pct, quelle = rech["tage"], rech["prozent"], "Rechnung"
    if zb and zb.get("skonto_tage"):
        if tage is None:
            tage, pct, quelle = int(zb["skonto_tage"]), float(zb["skonto_pct"]), f"Lieferantenstamm {zb['zb_code']}"
        elif (int(zb["skonto_tage"]), float(zb["skonto_pct"])) != (tage, pct):
            befunde.append(_befund("ZAHLUNGSBEDINGUNG_ABWEICHEND", f"Rechnung: {tage} Tage {pct:g} %, Stamm {zb['zb_code']}: {zb['text']}.", beleg, f"Lieferantenstamm {lief['lieferanten_nr']}"))
    elif zb and rech is None and not zb.get("skonto_tage") and extrakt.get("zahlungsbedingung_text"):
        pass
    if not tage:
        return {"moeglich": False, "zahlungsziel": extrakt.get("faellig_bis"), "hinweis": (zb or {}).get("text")}
    bis = _d(rech.get("bis")) if rech and rech.get("bis") else rdatum + timedelta(days=tage)
    lauf = bis
    while lauf.weekday() not in config.ZAHLUNGSLAUF_TAGE:
        lauf -= timedelta(days=1)
    freigabe_bis = lauf - timedelta(days=1)
    while freigabe_bis.weekday() >= 5:
        freigabe_bis -= timedelta(days=1)
    betrag = round(abs(extrakt.get("brutto") or 0) * pct / 100, 2)
    rest = (lauf - stichtag).days
    if 0 <= rest <= 4:
        befunde.append(_befund("SKONTO_FRIST_KNAPP", f"Skonto {_eur(betrag)} nur bei Zahlung im Lauf am {lauf:%d.%m.%Y}; Freigabe bis {freigabe_bis:%d.%m.%Y}.", beleg, None, betrag))
    return {"moeglich": True, "prozent": pct, "tage": tage, "betrag": betrag, "skonto_bis": bis.isoformat(),
            "letzter_zahlungslauf": lauf.isoformat(), "freigabe_spaetestens": freigabe_bis.isoformat(),
            "abgelaufen_bei_eingang": lauf < stichtag, "quelle": quelle}


def regelvorschlag(befunde: list[dict]) -> dict:
    """Baseline: schlechteste Empfehlung aller Befunde gewinnt."""
    entscheidung = "freigeben"
    for b in befunde:
        if regeln.STUFE[b["empfehlung"]] > regeln.STUFE[entscheidung]:
            entscheidung = b["empfehlung"]
    gruende = sorted([b for b in befunde if b["schwere"] != "info"],
                     key=lambda b: (-regeln.STUFE[b["empfehlung"]], b["schwere"] != "kritisch"))
    return {"entscheidung": entscheidung,
            "begruendungen": [{"code": b["code"], "text": b["text"], "beleg": b["beleg"], "bezug": b["bezug"], "betrag": b["betrag"]} for b in gruende]
            or [{"code": "OK", "text": "Alle Prüfungen ohne Beanstandung.", "beleg": None, "bezug": None, "betrag": None}]}
