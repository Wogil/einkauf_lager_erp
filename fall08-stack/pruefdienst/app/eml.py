"""E-Mail (.eml) zerlegen: Kopfzeilen, Text, Anhänge.

Inhalte der Mail werden nur gelesen und weitergereicht, nie interpretiert.
"""

from __future__ import annotations

import email
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email import policy
from email.utils import parseaddr, parsedate_to_datetime

RECHNUNGS_ENDUNGEN = (".pdf", ".xml")


@dataclass
class Anhang:
    dateiname: str
    mime: str
    inhalt: bytes

    @property
    def endung(self) -> str:
        return "." + self.dateiname.rsplit(".", 1)[-1].lower() if "." in self.dateiname else ""

    @property
    def ist_rechnungsdokument(self) -> bool:
        return self.endung in RECHNUNGS_ENDUNGEN


@dataclass
class Mail:
    message_id: str
    eingang: datetime
    absender: str
    absender_adresse: str
    absender_domain: str
    reply_to: str | None
    betreff: str
    text: str
    anhaenge: list[Anhang] = field(default_factory=list)
    sha256: str = ""

    @property
    def rechnungsanhaenge(self) -> list[Anhang]:
        return [a for a in self.anhaenge if a.ist_rechnungsdokument]

    @property
    def ist_rechnung(self) -> bool:
        return bool(self.rechnungsanhaenge)


def parse(raw: bytes) -> Mail:
    m = email.message_from_bytes(raw, policy=policy.default)
    absender = str(m.get("From", ""))
    adresse = parseaddr(absender)[1].lower()
    try:
        eingang = parsedate_to_datetime(str(m.get("Date")))
        if eingang.tzinfo is None:
            eingang = eingang.replace(tzinfo=timezone.utc)
    except Exception:
        eingang = datetime.now(timezone.utc)

    body = m.get_body(preferencelist=("plain", "html"))
    text = ""
    if body is not None:
        try:
            text = body.get_content()
        except Exception:
            text = ""

    anhaenge = []
    for teil in m.iter_attachments():
        name = teil.get_filename() or "anhang"
        inhalt = teil.get_payload(decode=True) or b""
        anhaenge.append(Anhang(name, teil.get_content_type(), inhalt))

    sha = hashlib.sha256(raw).hexdigest()
    reply = m.get("Reply-To")
    return Mail(
        message_id=str(m.get("Message-ID") or f"<ohne-id-{sha[:16]}>").strip(),
        eingang=eingang,
        absender=absender,
        absender_adresse=adresse,
        absender_domain=adresse.split("@")[-1] if "@" in adresse else "",
        reply_to=str(reply) if reply else None,
        betreff=str(m.get("Subject", "")),
        text=text,
        anhaenge=anhaenge,
        sha256=sha,
    )
