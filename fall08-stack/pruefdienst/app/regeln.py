"""Regelwerk: welcher Befund führt zu welcher Empfehlung.

Eine Stelle für alle Zuordnungen, damit das Team sie gegen die Evaluation justieren kann.
Grundlage: Freigaberichtlinie (2024), Prüfliste MB (14 Punkte), Kontierungsleitfaden, Brief Fall 08.
"""

# code: (schwere, empfehlung, kurztitel)
#   schwere:    info | warnung | kritisch
#   empfehlung: freigeben | klaeren | ablehnen
REGELN: dict[str, tuple[str, str, str]] = {
    # Echtheit / Betrug
    "LIEFERANT_UNBEKANNT":            ("kritisch", "ablehnen", "Rechnungssteller weder im Lieferantenstamm noch im Handelsregister"),
    "LIEFERANT_NEU":                  ("warnung",  "klaeren",  "Rechnungssteller nicht im Lieferantenstamm (Einkauf fragen)"),
    "LIEFERANT_GELOESCHT":            ("kritisch", "ablehnen", "Rechnungssteller im Handelsregister gelöscht"),
    "IBAN_ABWEICHUNG":                ("kritisch", "klaeren",  "Bankverbindung weicht vom Lieferantenstamm ab"),
    "IBAN_UNGUELTIG":                 ("kritisch", "klaeren",  "IBAN-Prüfziffer ungültig"),
    "IBAN_ANDERER_LIEFERANT":         ("kritisch", "klaeren",  "IBAN gehört laut Stamm zu einem anderen Lieferanten"),
    "BANK_BLZ_WIDERSPRUCH":           ("warnung",  "klaeren",  "Bankname/BIC passt nicht zur Bankleitzahl der IBAN"),
    "ABSENDER_DOMAIN_IMITAT":         ("kritisch", "klaeren",  "Absender-Domain imitiert die Domain des Lieferanten"),
    "ABSENDER_DOMAIN_FREMD":          ("warnung",  "klaeren",  "Absender-Domain gehört nicht zum Lieferanten"),
    "REPLY_TO_ABWEICHEND":            ("warnung",  "klaeren",  "Antwortadresse (Reply-To) weicht vom Absender ab"),
    "BANKAENDERUNG_MAIL_VORHER":      ("warnung",  "klaeren",  "Vorher ging eine Mail zur Bankänderung von ähnlicher Domain ein"),
    "BANKAENDERUNG_MAIL_HINWEIS":     ("info",     "freigeben", "Frühere Bankänderungs-Mail bekannt, diese Rechnung nutzt aber die Stamm-IBAN"),
    "REGISTER_ABWEICHUNG":            ("warnung",  "klaeren",  "Registerangabe auf der Rechnung passt nicht zum Handelsregister"),
    "REGISTERANGABE_FEHLT":           ("warnung",  "klaeren",  "Keine Registerangabe trotz eintragungspflichtiger Rechtsform"),
    "ANWEISUNG_IM_BELEG":             ("warnung",  "klaeren",  "Bemerkungsfeld enthält Anweisungen an automatisierte Systeme (ignoriert)"),
    "PDF_XML_WIDERSPRUCH":            ("kritisch", "klaeren",  "PDF und XML der Rechnung widersprechen sich"),

    # Formal
    "FALSCHER_EMPFAENGER":            ("kritisch", "ablehnen", "Rechnung an falsche Gesellschaft adressiert (§ 14 UStG)"),
    "PFLICHTANGABE_FEHLT":            ("kritisch", "ablehnen", "Pflichtangabe nach § 14 UStG fehlt"),
    "RECHNERISCH_FALSCH":             ("kritisch", "ablehnen", "Rechnung rechnerisch falsch"),
    "REVERSE_CHARGE_HINWEIS_FEHLT":   ("warnung",  "klaeren",  "Auslandslieferant ohne Hinweis auf Steuerschuldnerschaft"),

    # Dubletten
    "DUBLETTE":                       ("kritisch", "ablehnen", "Rechnung liegt bereits vor (gleicher Lieferant, gleiche Rechnungsnummer)"),
    "MOEGLICHE_DUBLETTE":             ("warnung",  "klaeren",  "Gleicher Betrag kurz zuvor bereits berechnet"),
    "KORREKTUR_ORIGINAL_BEZAHLT":     ("kritisch", "klaeren",  "Korrekturrechnung, Original wurde bereits bezahlt"),

    # Sachlich
    "BESTELLUNG_FEHLT":               ("warnung",  "klaeren",  "Keine Bestellnummer (Rückfrage beim Besteller)"),
    "BESTELLUNG_UNBEKANNT":           ("warnung",  "klaeren",  "Bestellnummer in WAVE nicht gefunden"),
    "BESTELLUNG_ANDERER_LIEFERANT":   ("kritisch", "klaeren",  "Bestellung gehört zu einem anderen Lieferanten"),
    "PREIS_ABWEICHUNG":               ("warnung",  "klaeren",  "Preis über Bestellung bzw. Preisvereinbarung"),
    "MENGE_UEBER_WARENEINGANG":       ("warnung",  "klaeren",  "Berechnete Menge größer als geliefert und noch nicht berechnet"),
    "WARENEINGANG_FEHLT":             ("warnung",  "klaeren",  "Zur Bestellung ist noch kein Wareneingang gebucht"),
    "ZUSCHLAG_NICHT_VEREINBART":      ("kritisch", "ablehnen", "Nicht vereinbarter Zuschlag berechnet"),
    "POSITION_OHNE_BESTELLBEZUG":     ("warnung",  "klaeren",  "Rechnungsposition ohne passende Bestellposition"),
    "GUTSCHRIFT_OHNE_BEZUG":          ("warnung",  "klaeren",  "Gutschrift ohne erkennbaren Bezug auf eine Rechnung"),
    "POSITIONEN_UNVOLLSTAENDIG":      ("warnung",  "klaeren",  "Positionen nicht vollständig gelesen (Summe ≠ Netto) – am Beleg prüfen"),
    "LESBARKEIT_UNSICHER":            ("warnung",  "klaeren",  "Dokument nur per Texterkennung gelesen, Werte unsicher"),

    # Hinweise (keine Beanstandung)
    "PREISVEREINBARUNG_ANGEWENDET":   ("info", "freigeben", "Preis entspricht der Preisvereinbarung 2026 (höher als Bestellpreis)"),
    "PREIS_UNTER_REFERENZ":           ("info", "freigeben", "Preis unter Bestellung/Preisvereinbarung"),
    "WIEDERKEHRENDE_LEISTUNG":        ("info", "freigeben", "Wiederkehrende Leistung ohne Bestellung (üblich bei diesem Lieferanten)"),
    "KORREKTUR_ERSETZT":              ("info", "freigeben", "Korrekturrechnung ersetzt eine frühere Rechnung"),
    "ZAHLUNGSBEDINGUNG_ABWEICHEND":   ("info", "freigeben", "Zahlungsbedingung auf der Rechnung weicht vom Stamm ab"),
    "DUPLIKAT_VERMERK":               ("info", "freigeben", "Dokument trägt Vermerk Duplikat/Kopie"),
    "SKONTO_FRIST_KNAPP":             ("info", "freigeben", "Skontofrist läuft bald ab"),
    "ANLAGEGUT_HINWEIS":              ("info", "freigeben", "Möglicherweise Anlagegut (> 800 € netto) – Anlagenbuchhaltung informieren"),
}

STUFE = {"freigeben": 0, "klaeren": 1, "ablehnen": 2}

ZUSCHLAG_WOERTER = r"zuschlag|express|\beil(?:fracht|lieferung|service)?\b|sonderfahrt|mindermenge"

ANWEISUNG_MUSTER = (
    r"ignor\w* (all|alle|previous|vorherig)|note to ai|ai assistant|ki-?assistent|"
    r"automatisierte (prüf|system)|mark .* as approved|bereits freigegeben|ohne abgleich|"
    r"sofort(ige)? zahlung|treat the invoice|system prompt"
)

# Fallback-Kontierung nach Lieferantengruppe (Kontierungsleitfaden SKR04, erste Zeile je Gruppe)
LEITFADEN = {
    "Arbeitskleidung": ("6850", "4200"), "Blech/Schacht": ("5100", "4100"), "Bürobedarf": ("6815", "7000"),
    "Chemikalien": ("5100", "4300"), "Dichtungen": ("5400", None), "Druckerei": ("6600", "2600"),
    "Elektronik": ("5100", "4100"), "Energie": ("6325", "8000"), "Entsorgung": ("6859", "4100"),
    "Frequenzumrichter": ("5400", None), "Gase": ("5100", "4100"), "Gebäudereinigung": ("6330", "8000"),
    "Guss": ("5100", "4100"), "Hydraulik": ("5100", "4100"), "IT-Dienstleister": ("6495", "7200"),
    "Kabel": ("5100", "4100"), "Kantine": ("6130", "7100"), "Kfz-Leasing": ("6560", "3200"),
    "Lager": ("5400", None), "Laufräder/Zerspanung": ("5100", "4100"), "Messebau": ("6610", "2600"),
    "Messtechnik": ("5100", "4100"), "Motoren": ("5100", "4100"), "Normteile": ("5100", "4100"),
    "Oberfläche": ("5900", None), "Prüfdienstleister": ("6470", "6000"), "Rechtsberatung": ("6825", "1000"),
    "Software": ("6495", "7200"), "Software_B": ("6837", "3100"), "Spedition": ("6740", "6200"),
    "Steuerberatung": ("6827", "7000"), "Telekommunikation": ("6805", "7200"), "Verpackung": ("6710", None),
    "Versicherung": ("6400", "1000"), "Werkzeuge": ("6845", "4100"), "Zeitarbeit": ("5900", "4200"),
}

# Freigabe 1.000–10.000 €: Abteilungsleitung der bestellenden Abteilung (Freigaberichtlinie 2.)
ABTEILUNGSLEITUNG = {
    "EK": "10011", "LG": "10011",   # Material/Logistik: Leiter Einkauf
    "SV": "10008",                  # Service
    "IT": "10016",                  # IT
    "PR": "10019",                  # Produktion
    "FI": "10012", "HR": "10012",   # Finanzen/Personal: Leiterin Rechnungswesen
    "QM": "10010",                  # Qualität
    "MK": "10017",                  # Marketing
    "EL": "10018", "VI": "10005", "EX": "10022", "VDS": "10020",
}
SACHBEARBEITUNG = "10013"           # Kreditorenbuchhaltung (Standard: Frau Brinkmann)
GF_KAUFMAENNISCH = [("10002", None, "2026-02-28"), ("10003", "2026-03-01", None)]
