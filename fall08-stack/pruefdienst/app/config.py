"""Konfiguration des Prüfdienstes (alles über Umgebungsvariablen)."""

import os
from pathlib import Path


def _env(name: str, default: str | None = None) -> str:
    wert = os.environ.get(name, default)
    if wert is None:
        raise RuntimeError(f"Umgebungsvariable {name} fehlt")
    return wert


# Datenbank mit Schema wave (WAVE-Export), ref (Register, ArchivPlus-Index) und app (Prüfdienst)
DATABASE_URL = _env("DATABASE_URL", "postgresql://postgres@localhost/vosskamp")

# Token, mit dem n8n und der SRW-Agent (MCP) sich anmelden
API_TOKEN = _env("PRUEFDIENST_TOKEN", "dev-token")

# Geheimnis für die signierten Entscheidungs-Links in den Mails
LINK_SECRET = _env("LINK_SECRET", "dev-link-secret")

# Öffentliche Basis-URL des n8n-Webhooks für Entscheidungen (Links in der Mail)
ENTSCHEIDUNG_URL = _env("ENTSCHEIDUNG_URL", "http://localhost:5678/webhook/entscheidung")

# Öffentliche Adresse des Prüfdienstes (Link „Rechnung ansehen“ in der Mail)
BELEG_URL = _env("BELEG_URL", "http://localhost:8000/beleg")

# Ablage für eingegangene Dokumente (unverändert, GoBD)
DOKUMENT_DIR = Path(_env("DOKUMENT_DIR", "/data/dokumente"))

# Registerauszüge (world/register) und Bankenliste (world/banks)
REGISTER_DIR = Path(_env("REGISTER_DIR", "/seed/register"))
BANKS_DIR = Path(_env("BANKS_DIR", "/seed/banks"))

# Eigene Gesellschaft (richtiger Rechnungsempfänger)
EIGENE_FIRMA = "Voßkamp Pumpenwerk GmbH & Co. KG"
EIGENE_DOMAIN = "vosskamp-pumpen.example"
FALSCHE_EMPFAENGER = ["Verwaltungs-GmbH", "Hellweg Dosiertechnik"]

# Freigabegrenzen brutto (Freigaberichtlinie 2024)
GRENZE_SACHBEARBEITUNG = 1000.00
GRENZE_ABTEILUNGSLEITUNG = 10000.00

# Toleranz Preisabweichung je Rechnung (Freigaberichtlinie: ±1 €)
PREIS_TOLERANZ_RECHNUNG = 1.00

# Zahlungsläufe (Wochentage: 0 = Montag)
ZAHLUNGSLAUF_TAGE = (1, 4)  # Dienstag, Freitag

REGELVERSION = "2026-11-03.2"
