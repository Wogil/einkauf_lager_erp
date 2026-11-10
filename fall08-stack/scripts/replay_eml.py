#!/usr/bin/env python3
"""Spielt .eml-Dateien in den Workflow ein – so, als kämen sie gerade im Postfach rechnungseingang@ an.

Beispiele:
  # die 96 Mails der INBOX (Stand 30.09.2026) über den n8n-Webhook einspielen
  python3 scripts/replay_eml.py ../companies/a_vosskamp/mail/eml/rechnungseingang@vosskamp-pumpen.example/INBOX

  # nur ausgewählte Demo-Fälle
  python3 scripts/replay_eml.py pfad/zu/2026-09-24_A-ER-003679.eml pfad/zu/2026-09-28_A-ER-003697.eml

  # ohne n8n direkt an den Prüfdienst (nur Regelprüfung, z. B. für Massentests)
  python3 scripts/replay_eml.py --direkt --token $PRUEFDIENST_TOKEN ORDNER

Die Mails werden chronologisch (nach Date-Header) eingespielt, damit z. B. eine Bankänderungs-Mail
vor der zugehörigen Rechnung im System ist.
"""

import argparse
import email
import json
import sys
import time
import urllib.request
import uuid
from email.utils import parsedate_to_datetime
from pathlib import Path


def dateien(pfade: list[str]) -> list[Path]:
    out = []
    for p in map(Path, pfade):
        out.extend(sorted(p.rglob("*.eml")) if p.is_dir() else [p])

    def datum(f: Path):
        try:
            with open(f, "rb") as fh:
                return parsedate_to_datetime(email.message_from_binary_file(fh)["Date"]).timestamp()
        except Exception:
            return 0
    return sorted(out, key=datum)


def multipart(feld: str, dateiname: str, inhalt: bytes) -> tuple[bytes, str]:
    grenze = uuid.uuid4().hex
    body = (f"--{grenze}\r\nContent-Disposition: form-data; name=\"{feld}\"; filename=\"{dateiname}\"\r\n"
            f"Content-Type: message/rfc822\r\n\r\n").encode() + inhalt + f"\r\n--{grenze}--\r\n".encode()
    return body, f"multipart/form-data; boundary={grenze}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pfade", nargs="+", help=".eml-Dateien oder Ordner")
    ap.add_argument("--webhook", default="http://localhost:5678/webhook/rechnungseingang", help="n8n-Webhook")
    ap.add_argument("--direkt", action="store_true", help="direkt an den Prüfdienst statt an n8n")
    ap.add_argument("--pruefdienst", default="http://localhost:8000")
    ap.add_argument("--token", default="", help="PRUEFDIENST_TOKEN (nur mit --direkt)")
    ap.add_argument("--pause", type=float, default=1.0, help="Sekunden zwischen zwei Mails")
    a = ap.parse_args()

    liste = dateien(a.pfade)
    print(f"{len(liste)} Mails")
    for i, f in enumerate(liste, 1):
        inhalt = f.read_bytes()
        if a.direkt:
            req = urllib.request.Request(f"{a.pruefdienst}/api/eingang", data=inhalt, method="POST",
                                         headers={"Content-Type": "message/rfc822", "Authorization": f"Bearer {a.token}"})
        else:
            body, ct = multipart("datei", f.name, inhalt)
            req = urllib.request.Request(a.webhook, data=body, method="POST", headers={"Content-Type": ct})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                antwort = json.loads(r.read() or b"{}")
            if a.direkt and antwort.get("vorgang_id"):
                rp = urllib.request.Request(f"{a.pruefdienst}/api/vorgang/{antwort['vorgang_id']}/regelpruefung", method="POST",
                                            headers={"Authorization": f"Bearer {a.token}"})
                with urllib.request.urlopen(rp, timeout=120) as r:
                    erg = json.loads(r.read())
                antwort["vorschlaege"] = [e["entscheidung"] for e in erg["ergebnisse"]]
            kurz = {k: antwort.get(k) for k in ("ist_rechnung", "vorgang_id", "vorschlaege", "status") if k in antwort}
            print(f"[{i}/{len(liste)}] {f.name}: {kurz or 'angenommen'}")
        except Exception as e:
            print(f"[{i}/{len(liste)}] {f.name}: FEHLER {e}", file=sys.stderr)
        time.sleep(a.pause)


if __name__ == "__main__":
    main()
