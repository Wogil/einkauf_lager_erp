"""Rechnungsdokumente lesen: XRechnung/ZUGFeRD (CII, UBL), PDF mit Text, gescannte PDF (OCR).

Ergebnis ist ein einheitlicher "Extrakt" (dict). Freitexte (Bemerkungen) landen in
`freitexte` und werden ausdrücklich als nicht vertrauenswürdige Daten markiert.
"""

from __future__ import annotations

import io
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from datetime import date, datetime
from pathlib import Path

GELD = r"-?\d{1,3}(?:\.\d{3})*,\d{2}"
DATUM = r"\d{2}\.\d{2}\.\d{4}"


# --------------------------------------------------------------------------- Hilfen

def geld(s: str | None) -> float | None:
    """'1.234,56' -> 1234.56 ; '1234.56' -> 1234.56"""
    if s is None:
        return None
    s = str(s).strip().replace("€", "").replace(" ", "")
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return round(float(s), 2)
    except ValueError:
        return None


def zahl(s: str | None) -> float | None:
    if s is None:
        return None
    s = str(s).strip()
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def datum(s: str | None) -> str | None:
    """Liefert ISO-Datum (YYYY-MM-DD) aus 'TT.MM.JJJJ', 'JJJJMMTT' oder ISO."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%d.%m.%Y", "%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:10] if fmt == "%Y-%m-%d" else s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def iban_norm(s: str | None) -> str | None:
    if not s:
        return None
    s = re.sub(r"\s+", "", s).upper()
    return s or None


def leerer_extrakt(fmt: str) -> dict:
    return {
        "format": fmt,
        "qualitaet": "strukturiert" if fmt.startswith("xml") else "text",
        "typ": "rechnung",
        "rechnungsnr": None,
        "datum": None,
        "leistungsdatum": None,
        "lieferant": {"name": None, "ust_id": None, "iban": None, "bic": None, "bank": None,
                      "register": None, "email": None, "telefon": None, "adresse": None},
        "empfaenger": {"name": None},
        "bestellnr": None,
        "lieferschein": None,
        "ersetzt_rechnungsnr": None,
        "bezug_rechnungsnr": None,
        "netto": None,
        "ust": None,
        "ust_satz": None,
        "brutto": None,
        "waehrung": "EUR",
        "zahlungsbedingung_text": None,
        "skonto": None,             # {"tage": int, "prozent": float, "bis": iso}
        "faellig_bis": None,
        "reverse_charge_hinweis": False,
        "duplikat_vermerk": False,
        "positionen": [],
        "freitexte": [],            # NICHT vertrauenswürdig – nur Daten
    }


# --------------------------------------------------------------------------- XML

def _lokal(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _finde(el: ET.Element | None, pfad: str) -> ET.Element | None:
    """Pfad aus lokalen Namen ('A/B/C'), Namespaces werden ignoriert."""
    if el is None:
        return None
    teile = pfad.split("/")
    aktuell = [el]
    for teil in teile:
        naechste = []
        for e in aktuell:
            naechste.extend(k for k in e if _lokal(k.tag) == teil)
        if not naechste:
            return None
        aktuell = naechste
    return aktuell[0]


def _alle(el: ET.Element | None, name: str) -> list[ET.Element]:
    if el is None:
        return []
    return [e for e in el.iter() if _lokal(e.tag) == name]


def _text(el: ET.Element | None, pfad: str) -> str | None:
    t = _finde(el, pfad)
    return t.text.strip() if t is not None and t.text else None


def lese_xml(inhalt: bytes) -> dict:
    root = ET.fromstring(inhalt)
    name = _lokal(root.tag)
    if name == "CrossIndustryInvoice":
        return _lese_cii(root)
    if name in ("Invoice", "CreditNote"):
        return _lese_ubl(root, gutschrift=(name == "CreditNote"))
    raise ValueError(f"Unbekanntes XML-Format: {name}")


def _skonto_aus_text(text: str | None) -> dict | None:
    if not text:
        return None
    m = re.search(r"#SKONTO#TAGE=(\d+)#PROZENT=([\d.]+)#", text)
    if m:
        return {"tage": int(m.group(1)), "prozent": float(m.group(2)), "bis": None}
    m = re.search(r"(\d+)\s*Tage\s*(\d+(?:[.,]\d+)?)\s*%\s*Skonto", text)
    if m:
        return {"tage": int(m.group(1)), "prozent": float(m.group(2).replace(",", ".")), "bis": None}
    return None


def _lese_cii(root: ET.Element) -> dict:
    x = leerer_extrakt("xml-cii")
    doc = _finde(root, "ExchangedDocument")
    x["rechnungsnr"] = _text(doc, "ID")
    typcode = _text(doc, "TypeCode")
    if typcode == "381":
        x["typ"] = "gutschrift"
    elif typcode == "384":
        x["typ"] = "korrektur"
    x["datum"] = datum(_text(doc, "IssueDateTime/DateTimeString"))
    for note in _alle(doc, "IncludedNote"):
        c = _text(note, "Content")
        if c:
            x["freitexte"].append(c)

    tx = _finde(root, "SupplyChainTradeTransaction")
    agr = _finde(tx, "ApplicableHeaderTradeAgreement")
    seller = _finde(agr, "SellerTradeParty")
    x["lieferant"]["name"] = _text(seller, "Name")
    for reg in _alle(seller, "SpecifiedTaxRegistration"):
        idel = _finde(reg, "ID")
        if idel is not None and idel.get("schemeID") == "VA":
            x["lieferant"]["ust_id"] = (idel.text or "").strip()
    adr = _finde(seller, "PostalTradeAddress")
    if adr is not None:
        x["lieferant"]["adresse"] = " ".join(filter(None, [_text(adr, "LineOne"), _text(adr, "PostcodeCode"), _text(adr, "CityName")]))
        x["lieferant"]["land"] = _text(adr, "CountryID")
    x["lieferant"]["email"] = _text(seller, "URIUniversalCommunication/URIID") or _text(seller, "DefinedTradeContact/EmailURIUniversalCommunication/URIID")
    x["empfaenger"]["name"] = _text(agr, "BuyerTradeParty/Name")
    x["bestellnr"] = _text(agr, "BuyerOrderReferencedDocument/IssuerAssignedID")

    dlv = _finde(tx, "ApplicableHeaderTradeDelivery")
    x["leistungsdatum"] = datum(_text(dlv, "ActualDeliverySupplyChainEvent/OccurrenceDateTime/DateTimeString"))
    x["lieferschein"] = _text(dlv, "DespatchAdviceReferencedDocument/IssuerAssignedID")

    st = _finde(tx, "ApplicableHeaderTradeSettlement")
    x["lieferant"]["iban"] = iban_norm(_text(st, "SpecifiedTradeSettlementPaymentMeans/PayeePartyCreditorFinancialAccount/IBANID"))
    x["lieferant"]["bic"] = _text(st, "SpecifiedTradeSettlementPaymentMeans/PayeeSpecifiedCreditorFinancialInstitution/BICID")
    terms = _text(st, "SpecifiedTradePaymentTerms/Description")
    x["zahlungsbedingung_text"] = terms
    x["skonto"] = _skonto_aus_text(terms)
    x["faellig_bis"] = datum(_text(st, "SpecifiedTradePaymentTerms/DueDateDateTime/DateTimeString"))
    ref = _text(st, "InvoiceReferencedDocument/IssuerAssignedID")
    if ref:
        x["bezug_rechnungsnr"] = ref
    tax = _finde(st, "ApplicableTradeTax")
    if tax is not None:
        x["ust_satz"] = zahl(_text(tax, "RateApplicablePercent"))
        if _text(tax, "CategoryCode") in ("AE", "K"):
            x["reverse_charge_hinweis"] = True
    summ = _finde(st, "SpecifiedTradeSettlementHeaderMonetarySummation")
    x["netto"] = geld(_text(summ, "TaxBasisTotalAmount"))
    x["ust"] = geld(_text(summ, "TaxTotalAmount"))
    x["brutto"] = geld(_text(summ, "GrandTotalAmount"))

    for i, li in enumerate(_alle(tx, "IncludedSupplyChainTradeLineItem"), 1):
        prod = _finde(li, "SpecifiedTradeProduct")
        menge_el = _finde(li, "SpecifiedLineTradeDelivery/BilledQuantity")
        x["positionen"].append({
            "pos": _text(li, "AssociatedDocumentLineDocument/LineID") or str(i),
            "art_nr_lieferant": _text(prod, "SellerAssignedID"),
            "art_nr_kunde": _text(prod, "BuyerAssignedID"),
            "bezeichnung": _text(prod, "Name"),
            "menge": zahl(menge_el.text) if menge_el is not None else None,
            "einheit": menge_el.get("unitCode") if menge_el is not None else None,
            "einzelpreis": geld(_text(li, "SpecifiedLineTradeAgreement/NetPriceProductTradePrice/ChargeAmount")),
            "betrag": geld(_text(li, "SpecifiedLineTradeSettlement/SpecifiedTradeSettlementLineMonetarySummation/LineTotalAmount")),
            "bestell_pos": _text(li, "SpecifiedLineTradeAgreement/BuyerOrderReferencedDocument/LineID"),
        })
        for note in _alle(li, "IncludedNote"):
            c = _text(note, "Content")
            if c:
                x["freitexte"].append(c)
    return x


def _lese_ubl(root: ET.Element, gutschrift: bool) -> dict:
    x = leerer_extrakt("xml-ubl")
    x["rechnungsnr"] = _text(root, "ID")
    typcode = _text(root, "InvoiceTypeCode") or _text(root, "CreditNoteTypeCode")
    if gutschrift or typcode == "381":
        x["typ"] = "gutschrift"
    elif typcode == "384":
        x["typ"] = "korrektur"
    x["datum"] = datum(_text(root, "IssueDate"))
    x["faellig_bis"] = datum(_text(root, "DueDate"))
    for k in root:
        if _lokal(k.tag) == "Note" and k.text:
            x["freitexte"].append(k.text.strip())
    x["bestellnr"] = _text(root, "OrderReference/ID") or _text(root, "BuyerReference")
    x["lieferschein"] = _text(root, "DespatchDocumentReference/ID")
    x["bezug_rechnungsnr"] = _text(root, "BillingReference/InvoiceDocumentReference/ID")

    sup = _finde(root, "AccountingSupplierParty/Party")
    x["lieferant"]["name"] = _text(sup, "PartyLegalEntity/RegistrationName") or _text(sup, "PartyName/Name")
    x["lieferant"]["ust_id"] = _text(sup, "PartyTaxScheme/CompanyID")
    x["lieferant"]["email"] = _text(sup, "EndpointID") or _text(sup, "Contact/ElectronicMail")
    x["lieferant"]["telefon"] = _text(sup, "Contact/Telephone")
    adr = _finde(sup, "PostalAddress")
    if adr is not None:
        x["lieferant"]["adresse"] = " ".join(filter(None, [_text(adr, "StreetName"), _text(adr, "PostalZone"), _text(adr, "CityName")]))
        x["lieferant"]["land"] = _text(adr, "Country/IdentificationCode")
    cus = _finde(root, "AccountingCustomerParty/Party")
    x["empfaenger"]["name"] = _text(cus, "PartyLegalEntity/RegistrationName") or _text(cus, "PartyName/Name")

    x["leistungsdatum"] = datum(_text(root, "Delivery/ActualDeliveryDate"))
    pm = _finde(root, "PaymentMeans")
    x["lieferant"]["iban"] = iban_norm(_text(pm, "PayeeFinancialAccount/ID"))
    x["lieferant"]["bic"] = _text(pm, "PayeeFinancialAccount/FinancialInstitutionBranch/ID")
    terms = _text(root, "PaymentTerms/Note")
    x["zahlungsbedingung_text"] = terms
    x["skonto"] = _skonto_aus_text(terms)

    tt = _finde(root, "TaxTotal")
    x["ust"] = geld(_text(tt, "TaxAmount"))
    cat = _finde(tt, "TaxSubtotal/TaxCategory")
    if cat is not None:
        x["ust_satz"] = zahl(_text(cat, "Percent"))
        if _text(cat, "ID") in ("AE", "K"):
            x["reverse_charge_hinweis"] = True
    lmt = _finde(root, "LegalMonetaryTotal")
    x["netto"] = geld(_text(lmt, "TaxExclusiveAmount"))
    x["brutto"] = geld(_text(lmt, "TaxInclusiveAmount")) or geld(_text(lmt, "PayableAmount"))

    for k in root:
        if _lokal(k.tag) not in ("InvoiceLine", "CreditNoteLine"):
            continue
        menge_el = _finde(k, "InvoicedQuantity")
        if menge_el is None:
            menge_el = _finde(k, "CreditedQuantity")
        x["positionen"].append({
            "pos": _text(k, "ID"),
            "art_nr_lieferant": _text(k, "Item/SellersItemIdentification/ID"),
            "art_nr_kunde": _text(k, "Item/BuyersItemIdentification/ID"),
            "bezeichnung": _text(k, "Item/Name"),
            "menge": zahl(menge_el.text) if menge_el is not None else None,
            "einheit": menge_el.get("unitCode") if menge_el is not None else None,
            "einzelpreis": geld(_text(k, "Price/PriceAmount")),
            "betrag": geld(_text(k, "LineExtensionAmount")),
            "bestell_pos": _text(k, "OrderLineReference/LineID"),
        })
        for n in k:
            if _lokal(n.tag) == "Note" and n.text:
                x["freitexte"].append(n.text.strip())
    if x["typ"] == "gutschrift":
        for feld in ("netto", "ust", "brutto"):
            if x[feld] is not None and x[feld] > 0:
                x[feld] = -x[feld]
    return x


# --------------------------------------------------------------------------- PDF

def pdf_text(inhalt: bytes) -> tuple[str, int]:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
        f.write(inhalt)
        f.flush()
        out = subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, text=True, timeout=60).stdout
        info = subprocess.run(["pdfinfo", f.name], capture_output=True, text=True, timeout=30).stdout
    m = re.search(r"Pages:\s+(\d+)", info)
    return out.replace("u0026", "&"), int(m.group(1)) if m else 1


def pdf_ocr(inhalt: bytes) -> str:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "in.pdf"
        p.write_bytes(inhalt)
        subprocess.run(["pdftoppm", "-r", "250", "-png", str(p), str(Path(d) / "seite")], check=True, timeout=120)
        texte = []
        for bild in sorted(Path(d).glob("seite*.png")):
            r = subprocess.run(["tesseract", str(bild), "-", "-l", "deu", "--psm", "6"], capture_output=True, text=True, timeout=120)
            texte.append(r.stdout)
    return "\n".join(texte)


def pdf_seitenbild(inhalt: bytes, seite: int = 1, dpi: int = 150) -> bytes:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "in.pdf"
        p.write_bytes(inhalt)
        subprocess.run(["pdftoppm", "-r", str(dpi), "-png", "-f", str(seite), "-l", str(seite), "-singlefile", str(p), str(Path(d) / "s")], check=True, timeout=60)
        return (Path(d) / "s.png").read_bytes()


def pdf_eingebettete_xml(inhalt: bytes) -> list[tuple[str, bytes]]:
    """ZUGFeRD/Factur-X: eingebettete XML-Dateien aus dem PDF holen."""
    try:
        from pypdf import PdfReader
        r = PdfReader(io.BytesIO(inhalt))
        out = []
        for name, daten in (r.attachments or {}).items():
            if name.lower().endswith(".xml"):
                out.extend((name, d) for d in daten)
        return out
    except Exception:
        return []


def _such(muster: str, text: str, flags: int = re.I) -> str | None:
    m = re.search(muster, text, flags)
    return m.group(1).strip() if m else None


_CODE = re.compile(r"^[A-Z]{0,3}\d{3,}(?:-\d+)?$")
_POS = re.compile(
    r"^\s*(\d{1,3})\.?\s+(.+?)\s+(-?\d+(?:[.,]\d+)?)\s*([A-Za-zÄÖÜäöüß.]{1,8})?\s+(" + GELD + r"|-?\d+,\d{3,4})\s+(" + GELD + r")\s*$"
)


def lese_pdf_text(text: str, fmt: str = "pdf-text") -> dict:
    x = leerer_extrakt(fmt)
    if fmt == "pdf-scan":
        x["qualitaet"] = "ocr"
    zeilen = [z.rstrip() for z in text.splitlines()]
    nichtleer = [z.strip() for z in zeilen if z.strip()]

    x["lieferant"]["name"] = nichtleer[0] if nichtleer else None
    kopf = "\n".join(nichtleer[:20])
    if re.search(r"\bGutschrift\b", kopf):
        x["typ"] = "gutschrift"
    if re.search(r"Rechnungskorrektur|Korrekturrechnung", kopf, re.I):
        x["typ"] = "korrektur"
    if re.search(r"DUPLIKAT|\bKopie\b|Zweitschrift", kopf, re.I):
        x["duplikat_vermerk"] = True

    rnr = _such(r"(?:Rechnungs|Gutschrifts?)(?:nummer|-?Nr\.?)[ \t]*:?[ \t]*([^\n]+)", text)
    if rnr:
        rnr = re.split(r"\s{2,}", rnr.strip())[0]
    x["rechnungsnr"] = rnr
    x["datum"] = datum(_such(r"(?:Rechnungs|Gutschrifts?)datum\s*:?\s*(" + DATUM + ")", text))
    x["leistungsdatum"] = datum(_such(r"(?:Leistungs|Liefer)datum\s*:?\s*(" + DATUM + ")", text))
    x["bestellnr"] = _such(r"Ihre Bestellung\s*:?\s*(\S+)", text) or _such(r"\b(BE\d{2}-\d{5})\b", text, 0)
    x["lieferschein"] = _such(r"Lieferschein(?:-?Nr\.?)?\s*:?\s*([A-Z0-9][\w\-/]*)", text)
    x["ersetzt_rechnungsnr"] = _such(r"Ersetzt Rechnung\s*:?\s*(\S+)", text)
    x["bezug_rechnungsnr"] = _such(r"(?:zu|Bezug(?:\s+auf)?)\s+Rechnung\s*(?:Nr\.?)?\s*:?\s*([A-Z0-9][\w/\-]*)", text)
    if x["bezug_rechnungsnr"] == x["rechnungsnr"]:
        x["bezug_rechnungsnr"] = None

    x["netto"] = geld(_such(r"Nettobetrag\s*:?\s*(" + GELD + ")", text))
    ust = re.search(r"(\d{1,2})\s*%\s*USt\s*:?\s*(" + GELD + ")", text)
    if ust:
        x["ust_satz"] = float(ust.group(1))
        x["ust"] = geld(ust.group(2))
    x["brutto"] = geld(_such(r"(?:Rechnungsbetrag|Gutschriftsbetrag|Gesamtbetrag|Bruttobetrag)\s*:?\s*(" + GELD + ")", text))

    x["lieferant"]["ust_id"] = _such(r"USt-?Id(?:Nr)?\.?\s*:?\s*(DE\s?\d{9})", text)
    if x["lieferant"]["ust_id"]:
        x["lieferant"]["ust_id"] = x["lieferant"]["ust_id"].replace(" ", "")
    x["lieferant"]["steuernummer"] = _such(r"Steuer-?(?:nummer|nr\.?)\s*:?\s*([\d/ ]{8,})", text)
    x["lieferant"]["iban"] = iban_norm(_such(r"IBAN\s*:?\s*([A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?[A-Z0-9]{1,4})?)", text))
    x["lieferant"]["bic"] = _such(r"BIC\s*:?\s*([A-Z]{6}[A-Z0-9]{2,5})", text)
    x["lieferant"]["bank"] = _such(r"Bankverbindung\s*:?\s*(.+?)\s*[·|\-]\s*IBAN", text)
    x["lieferant"]["telefon"] = _such(r"Tel\.?\s*(\+?[\d\s/\-]{6,})", text)
    x["lieferant"]["email"] = _such(r"([\w.\-]+@[\w.\-]+\.[a-z]{2,})", text)
    reg = re.search(r"Amtsgericht\s+([A-ZÄÖÜ][\w ()\-.äöüß]+?)\s+(HRA|HRB|GnR|PR|VR)\s*(\d+)", text)
    if reg:
        x["lieferant"]["register"] = {"gericht": reg.group(1).strip(), "art": reg.group(2), "nummer": reg.group(3)}

    for z in nichtleer[:15]:
        if re.search(r"Voßkamp|Vosskamp|Vo.kamp|Hellweg Dosiertechnik", z) and "Kreditoren" not in z:
            x["empfaenger"]["name"] = z
            break

    zb = _such(r"((?:Zahlungsbedingung|Zahlbar|Zahlungsziel)[^\n]+)", text)
    x["zahlungsbedingung_text"] = zb
    x["skonto"] = _skonto_aus_text(zb)
    if x["skonto"]:
        x["skonto"]["bis"] = datum(_such(r"Skontofrist bis\s*(" + DATUM + ")", text))
    x["faellig_bis"] = datum(_such(r"Zahlbar bis\s*(" + DATUM + ")", text))
    if re.search(r"Steuerschuldnerschaft des Leistungsempf|reverse charge|§\s*13b", text, re.I):
        x["reverse_charge_hinweis"] = True

    # Positionen: zwischen Tabellenkopf und Nettobetrag
    in_tabelle = False
    letzte = None
    zeilen = _umbrueche_zusammenfuehren(zeilen)
    for z in zeilen:
        if re.search(r"\bBezeichnung\b", z) and re.search(r"Meng|Anz", z):
            in_tabelle = True
            continue
        if re.search(r"Nettobetrag|Zwischensumme|Übertrag", z):
            in_tabelle = False
            letzte = None
            continue
        if not in_tabelle or not z.strip():
            continue
        m = _POS.match(z)
        if m:
            mitte = [t for t in re.split(r"\s{2,}", m.group(2).strip()) if t]
            codes = [t for t in mitte if _CODE.match(t)]
            text_teile = [t for t in mitte if not _CODE.match(t)]
            art_l, art_k = None, None
            for c in codes:
                if re.fullmatch(r"[24]\d{6}", c):
                    art_k = c
                else:
                    art_l = art_l or c
            letzte = {
                "pos": m.group(1),
                "art_nr_lieferant": art_l,
                "art_nr_kunde": art_k,
                "bezeichnung": " ".join(text_teile),
                "menge": zahl(m.group(3)),
                "einheit": m.group(4),
                "einzelpreis": geld(m.group(5)),
                "betrag": geld(m.group(6)),
                "bestell_pos": None,
            }
            x["positionen"].append(letzte)
        elif letzte is not None and not re.search(r"Seite \d+ von \d+", z):
            # Fortsetzungszeile (umgebrochene Bezeichnung oder Art.-Nr.)
            teile = [t for t in re.split(r"\s{2,}", z.strip()) if t]
            for t in teile:
                if letzte["einheit"] and re.fullmatch(r"[a-zäöü]{1,2}", t):
                    letzte["einheit"] += t
                elif letzte["art_nr_lieferant"] and re.fullmatch(r"\d{1,3}", t) and not letzte["bezeichnung"].endswith(t):
                    letzte["art_nr_lieferant"] += t
                else:
                    letzte["bezeichnung"] = (letzte["bezeichnung"] + " " + t).strip()

    if x["typ"] == "gutschrift":
        for feld in ("netto", "ust", "brutto"):
            if x[feld] is not None and x[feld] > 0:
                x[feld] = -x[feld]
    return x


def _umbrueche_zusammenfuehren(zeilen: list[str]) -> list[str]:
    """Manche Lieferanten brechen Beträge in schmalen Spalten um ('22.359,6' + Folgezeile '…   8'),
    teils Preis UND Betrag. Die abgeschnittenen Ziffern werden zurückgehängt und aus der Folgezeile entfernt."""
    out = list(zeilen)
    for i in range(len(out) - 1):
        if not re.match(r"^\s*\d{1,3}\.?\s", out[i]):
            continue
        # bis zu zwei abgeschnittene Beträge am Zeilenende (Preis und Betrag)
        m = re.search(r"(?:(\d[\d.]*,\d)(\s+))?(\d[\d.]*,\d)\s*$", out[i])
        if not m:
            continue
        j = i + 1
        while j < len(out) and not out[j].strip():
            j += 1
        if j >= len(out):
            continue
        n = re.search(r"\s(\d)\s+(\d)\s*$", out[j]) if m.group(1) else None
        if n and n.start(2) >= len(out[i].rstrip()) - 3:
            out[i] = out[i][:m.end(1)] + n.group(1) + m.group(2) + m.group(3) + n.group(2)
            out[j] = out[j][:n.start(1)].rstrip()
            continue
        n = re.search(r"\s(\d)\s*$", out[j])
        if n and n.start(1) >= len(out[i].rstrip()) - 3:
            out[i] = out[i].rstrip() + n.group(1)
            out[j] = out[j][:n.start(1)].rstrip()
    return out


# --------------------------------------------------------------------------- Einstieg

def analysiere(dateiname: str, inhalt: bytes) -> dict:
    """Liefert {format, text, seiten, extrakte:[...]}.

    Ein PDF kann eingebettete XML enthalten (ZUGFeRD) – dann werden beide gelesen.
    """
    name = dateiname.lower()
    if name.endswith(".xml"):
        return {"format": None, "text": inhalt.decode("utf-8", "replace"), "seiten": None,
                "extrakte": [lese_xml(inhalt)]}
    if name.endswith(".pdf"):
        text, seiten = pdf_text(inhalt)
        fmt = "pdf-text"
        if len(re.sub(r"\s", "", text)) < 80:
            fmt = "pdf-scan"
            text = pdf_ocr(inhalt)
        extrakte = [lese_pdf_text(text, fmt)]
        for xname, xinhalt in pdf_eingebettete_xml(inhalt):
            try:
                e = lese_xml(xinhalt)
                e["eingebettet_in_pdf"] = True
                extrakte.append(e)
            except Exception:
                pass
        return {"format": fmt, "text": text, "seiten": seiten, "extrakte": extrakte}
    raise ValueError(f"Kein Rechnungsdokument: {dateiname}")
