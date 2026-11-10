#!/usr/bin/env python3
"""Liest alle Rechnungsdokumente eines ArchivPlus-Monats (oder mehrerer) und misst, wie vollständig
der Parser die Pflichtfelder erkennt. Braucht nur Python + pdftotext (poppler), keine Datenbank.

  python3 tests/parser_massentest.py ../companies/a_vosskamp/archivplus/Eingangsrechnungen/2026/2026-09
"""

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pruefdienst"))
from app import dokument  # noqa: E402

FELDER = ["rechnungsnr", "datum", "brutto", "netto", "iban", "ust_id", "bestellnr", "positionen", "summe_passt"]


def pruefe(ordner: list[str], ocr: bool = False):
    zaehler = {fmt: Counter() for fmt in ("xml-cii", "xml-ubl", "pdf-text", "pdf-scan")}
    anzahl = Counter()
    fehler = []
    for o in ordner:
        for f in sorted(Path(o).rglob("*")):
            if f.suffix.lower() not in (".pdf", ".xml"):
                continue
            try:
                if f.suffix.lower() == ".pdf" and not ocr:
                    text, _ = dokument.pdf_text(f.read_bytes())
                    if len(text.replace(" ", "").replace("\n", "")) < 80:
                        anzahl["pdf-scan (übersprungen)"] += 1
                        continue
                    x = dokument.lese_pdf_text(text)
                else:
                    x = dokument.analysiere(f.name, f.read_bytes())["extrakte"][0]
            except Exception as e:
                fehler.append((f.name, str(e)[:80]))
                continue
            fmt = x["format"]
            anzahl[fmt] += 1
            z = zaehler[fmt]
            z["rechnungsnr"] += bool(x.get("rechnungsnr"))
            z["datum"] += bool(x.get("datum"))
            z["brutto"] += x.get("brutto") is not None
            z["netto"] += x.get("netto") is not None
            z["iban"] += bool(x["lieferant"].get("iban"))
            z["ust_id"] += bool(x["lieferant"].get("ust_id") or x["lieferant"].get("steuernummer"))
            z["bestellnr"] += bool(x.get("bestellnr"))
            z["positionen"] += bool(x.get("positionen"))
            summe = round(sum(p.get("betrag") or 0 for p in x.get("positionen") or []), 2)
            z["summe_passt"] += x.get("netto") is not None and abs(summe - x["netto"]) <= 0.05
    print(f"{'Format':<12}" + "".join(f"{f:>12}" for f in ["Anzahl"] + FELDER))
    for fmt, z in zaehler.items():
        n = anzahl[fmt]
        if n:
            print(f"{fmt:<12}{n:>12}" + "".join(f"{100 * z[f] / n:>11.0f}%" for f in FELDER))
    for k, v in anzahl.items():
        if k not in zaehler:
            print(f"{k}: {v}")
    if fehler:
        print(f"\n{len(fehler)} Dokumente nicht lesbar, z. B.:", fehler[:5])


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    pruefe(args, ocr="--ocr" in sys.argv)
