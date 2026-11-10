#!/usr/bin/env python3
"""Erzeugt die n8n-Workflow-Dateien (JSON) in n8n/workflows/.

Die Workflows werden beim Start des n8n-Containers automatisch importiert (n8n/start.sh).
Änderungen am besten in n8n selbst vornehmen und mit „Download“ wieder hier ablegen –
dieses Skript ist nur der reproduzierbare Ausgangsstand.
"""

import json
import uuid
from pathlib import Path

OUT = Path(__file__).parent / "workflows"
AUTH = {"parameters": [{"name": "Authorization", "value": "=Bearer {{ $env.PRUEFDIENST_TOKEN }}"}]}
SRW_AUTH = {"parameters": [{"name": "Authorization", "value": "=Bearer {{ $env.SRW_API_KEY }}"}]}


def node(name, typ, version, pos, params, **extra):
    n = {"parameters": params, "name": name, "type": typ, "typeVersion": version, "position": pos,
         "id": str(uuid.uuid5(uuid.NAMESPACE_URL, "fall08/" + name))}
    n.update(extra)
    return n


def http(name, pos, method, url, body=None, headers=AUTH, timeout=120000, **extra):
    p = {"method": method, "url": url, "sendHeaders": True, "headerParameters": headers, "options": {"timeout": timeout}}
    if body is not None:
        p.update({"sendBody": True, "specifyBody": "json", "jsonBody": body})
    return node(name, "n8n-nodes-base.httpRequest", 4.2, pos, p, **extra)


def wenn(name, pos, ausdruck):
    return node(name, "n8n-nodes-base.if", 2, pos, {
        "conditions": {"options": {"caseSensitive": True, "leftValue": "", "typeValidation": "loose"},
                       "conditions": [{"id": "b1", "leftValue": ausdruck, "rightValue": "",
                                       "operator": {"type": "boolean", "operation": "true", "singleValue": True}}],
                       "combinator": "and"},
        "options": {}})


def code(name, pos, js):
    return node(name, "n8n-nodes-base.code", 2, pos, {"jsCode": js})


def verbinde(*kanten):
    """kanten: (von, nach) oder (von, nach, ausgang)"""
    c = {}
    for k in kanten:
        von, nach, aus = (k + (0,))[:3]
        c.setdefault(von, {"main": []})
        while len(c[von]["main"]) <= aus:
            c[von]["main"].append([])
        c[von]["main"][aus].append({"node": nach, "type": "main", "index": 0})
    return c


VORGANG = "$('Prüfdienst: Mail einliefern').item.json.vorgang_id"

# =========================================================================== Workflow 1: Rechnungseingang

eingang_nodes = [
    node("Webhook: .eml einliefern", "n8n-nodes-base.webhook", 2, [0, 0],
         {"httpMethod": "POST", "path": "rechnungseingang", "responseMode": "onReceived",
          "responseData": "allEntries", "options": {"rawBody": False}}, webhookId="5e0c7d4e-08a1-4c1e-9d55-rechnungsein"),
    node("IMAP: Postfach rechnungseingang@", "n8n-nodes-base.emailReadImap", 2, [0, 220],
         {"mailbox": "INBOX", "postProcessAction": "nothing", "format": "raw", "options": {}},
         disabled=True, notes="Für den Echtbetrieb: IMAP-Zugangsdaten hinterlegen und Knoten aktivieren."),
    code("Eml aus Upload", [240, 0], """// .eml aus dem Upload (Feld "datei") als Base64 an den Prüfdienst geben – Inhalt wird hier nicht gelesen
const out = [];
const items = $input.all();
for (let i = 0; i < items.length; i++) {
  const keys = Object.keys(items[i].binary || {});
  if (!keys.length) throw new Error('Keine .eml im Request (multipart-Feld "datei" erwartet)');
  const buf = await this.helpers.getBinaryDataBuffer(i, keys[0]);
  out.push({ json: { raw_base64: buf.toString('base64'), quelle: 'email' } });
}
return out;"""),
    code("Eml aus IMAP", [240, 220], """return $input.all().map(i => ({ json: { raw_base64: i.json.raw, quelle: 'email' } }));"""),
    http("Prüfdienst: Mail einliefern", [480, 100], "POST", "={{ $env.PRUEFDIENST_URL }}/api/eingang",
         "={{ JSON.stringify({ raw_base64: $json.raw_base64, quelle: $json.quelle }) }}"),
    wenn("Enthält Rechnung?", [720, 100], "={{ $json.ist_rechnung === true }}"),
    node("Keine Rechnung – nur protokolliert", "n8n-nodes-base.noOp", 1, [960, 260], {}),
    wenn("Schon verarbeitet?", [960, 40], "={{ $json.bereits_verarbeitet === true }}"),
    node("Bereits verarbeitet – übersprungen", "n8n-nodes-base.noOp", 1, [1200, 300], {},
         notes="Gleiche Message-ID wurde schon geprüft. Zum erneuten Testen: scripts/reset_testdaten.sh"),
    wenn("Modus SRW?", [1200, 0], "={{ $env.PRUEFMODUS === 'srw' }}"),

    # --- Modus regeln (Baseline)
    http("Regelprüfung (Baseline)", [1200, 160], "POST", f"={{{{ $env.PRUEFDIENST_URL }}}}/api/vorgang/{{{{ {VORGANG} }}}}/regelpruefung"),

    # --- Modus srw
    http("SRW: Job starten", [1200, -160], "POST", "={{ $env.SRW_API_URL }}/api/jobs", (
        "={{ JSON.stringify({"
        " description: 'Eingangsrechnung prüfen – Vorgang ' + $json.vorgang_id + ' (' + ($json.rechnungen || []).length + ' Rechnung/en)',"
        " expert: $env.SRW_EXPERT,"
        " project_id: $env.SRW_PROJECT_ID || undefined,"
        " workspace: null,"
        " use_datasource_defaults: true,"
        " kickoff_message: 'Prüfe Vorgang ' + $json.vorgang_id + ' mit den MCP-Tools des Prüfdienstes: lese_vorgang, pruefe_rechnung je Rechnung, speichere_vorschlag je Rechnung. Gib bei speichere_vorschlag srw_job_id nicht an, wenn du sie nicht kennst.',"
        " context: { vorgang_id: $json.vorgang_id, rechnungen: $json.rechnungen }"
        " }) }}"), headers=SRW_AUTH),
    http("Job-ID beim Vorgang merken", [1440, -160], "POST", f"={{{{ $env.PRUEFDIENST_URL }}}}/api/vorgang/{{{{ {VORGANG} }}}}/srw-job",
         "={{ JSON.stringify({ job_id: $json.id || $json.job_id }) }}"),
    node("30 s warten", "n8n-nodes-base.wait", 1.1, [1680, -160], {"amount": 30, "unit": "seconds"}, webhookId="7a1f3c22-wait-srw-job-0000-000000000001"),
    http("SRW: Job-Status", [1920, -160], "GET", "={{ $env.SRW_API_URL }}/api/jobs/{{ $('SRW: Job starten').item.json.id || $('SRW: Job starten').item.json.job_id }}", headers=SRW_AUTH),
    wenn("Job fertig?", [2160, -160], "={{ ['completed','pending_review','failed','cancelled'].includes($json.status) || $runIndex >= 60 }}"),
    http("Vorschläge vorhanden?", [2400, -160], "GET", f"={{{{ $env.PRUEFDIENST_URL }}}}/api/vorgang/{{{{ {VORGANG} }}}}"),
    wenn("Agent hat alle Vorschläge gespeichert?", [2640, -160], "={{ $json.vollstaendig === true }}"),
    http("Rückfallebene: Regelprüfung", [2880, -40], "POST", f"={{{{ $env.PRUEFDIENST_URL }}}}/api/vorgang/{{{{ {VORGANG} }}}}/regelpruefung"),

    # --- Benachrichtigen
    http("Benachrichtigungen holen", [3120, 40], "GET", f"={{{{ $env.PRUEFDIENST_URL }}}}/api/vorgang/{{{{ {VORGANG} }}}}/benachrichtigungen",
         executeOnce=True),
    node("Je Rechnung", "n8n-nodes-base.splitOut", 1, [3360, 40], {"fieldToSplitOut": "benachrichtigungen", "options": {}}),
    http("Mail an zuständige Person", [3600, 40], "POST", "={{ $env.MAIL_API_URL }}", (
        "={{ JSON.stringify({"
        " From: { Email: $env.MAIL_ABSENDER, Name: 'Rechnungsprüfung (Fall 08)' },"
        " To: [ { Email: $json.an_email, Name: $json.an_name } ],"
        " Subject: $json.betreff,"
        " HTML: $json.html,"
        " Tags: [ $json.entscheidung ]"
        " }) }}"), headers={"parameters": []},
         notes="Prototyp: Versand über die Mailpit-API. Im Echtbetrieb durch „Send Email“ (SMTP), Outlook oder Teams ersetzen – der Inhalt kommt fertig vom Prüfdienst."),
]
eingang_conn = verbinde(
    ("Webhook: .eml einliefern", "Eml aus Upload"),
    ("IMAP: Postfach rechnungseingang@", "Eml aus IMAP"),
    ("Eml aus Upload", "Prüfdienst: Mail einliefern"),
    ("Eml aus IMAP", "Prüfdienst: Mail einliefern"),
    ("Prüfdienst: Mail einliefern", "Enthält Rechnung?"),
    ("Enthält Rechnung?", "Schon verarbeitet?", 0),
    ("Enthält Rechnung?", "Keine Rechnung – nur protokolliert", 1),
    ("Schon verarbeitet?", "Bereits verarbeitet – übersprungen", 0),
    ("Schon verarbeitet?", "Modus SRW?", 1),
    ("Modus SRW?", "SRW: Job starten", 0),
    ("Modus SRW?", "Regelprüfung (Baseline)", 1),
    ("SRW: Job starten", "Job-ID beim Vorgang merken"),
    ("Job-ID beim Vorgang merken", "30 s warten"),
    ("30 s warten", "SRW: Job-Status"),
    ("SRW: Job-Status", "Job fertig?"),
    ("Job fertig?", "Vorschläge vorhanden?", 0),
    ("Job fertig?", "30 s warten", 1),
    ("Vorschläge vorhanden?", "Agent hat alle Vorschläge gespeichert?"),
    ("Agent hat alle Vorschläge gespeichert?", "Benachrichtigungen holen", 0),
    ("Agent hat alle Vorschläge gespeichert?", "Rückfallebene: Regelprüfung", 1),
    ("Rückfallebene: Regelprüfung", "Benachrichtigungen holen"),
    ("Regelprüfung (Baseline)", "Benachrichtigungen holen"),
    ("Benachrichtigungen holen", "Je Rechnung"),
    ("Je Rechnung", "Mail an zuständige Person"),
)

# =========================================================================== Workflow 2: Entscheidung

SEITE = r"""const q = $('Webhook: Entscheidung').first().json.query || {};
const r = $input.first().json;
const LABEL = { freigeben: 'Freigeben', klaeren: 'Klären', ablehnen: 'Ablehnen', vorschlag_falsch: 'Vorschlag war falsch' };
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
let inhalt;
if (r.error || (!r.entscheidung_id && !r.formular)) {
  inhalt = `<h2>Das hat nicht geklappt</h2><p>Der Link ist ungültig oder wurde verändert. Bitte den Link aus der Mail unverändert öffnen.</p>`;
} else if (r.formular) {
  inhalt = `<h2>Danke für die Rückmeldung</h2><p>Was war am Vorschlag falsch? (hilft, den Agenten zu verbessern)</p>
  <form method="get"><input type="hidden" name="r" value="${esc(q.r)}"><input type="hidden" name="a" value="vorschlag_falsch"><input type="hidden" name="t" value="${esc(q.t)}">
  <textarea name="k" rows="4" style="width:100%;font:inherit"></textarea><p><button style="padding:8px 14px">Absenden</button></p></form>`;
} else if (r.aktion === 'vorschlag_falsch') {
  inhalt = `<h2>Danke!</h2><p>Ihre Rückmeldung zum Vorschlag wurde gespeichert und fließt in die Verbesserung der Prüfung ein.</p>
  <p>Ihre eigentliche Entscheidung treffen Sie bitte über die Knöpfe in der Mail.</p>`;
} else {
  const passt = r.uebereinstimmung ? 'entspricht dem Vorschlag' : `weicht vom Vorschlag „${esc(LABEL[r.vorschlag] || r.vorschlag)}“ ab`;
  inhalt = `<h2>Gespeichert: ${esc(LABEL[r.aktion] || r.aktion)}</h2><p>Ihre Entscheidung ${passt}. Sie wurde mit Zeitpunkt protokolliert.</p>
  <p style="color:#76746e">Buchung und Zahlung erfolgen wie gewohnt in WAVE und ZahlWerk.</p>`;
}
return [{ json: { ...r, html: `<!doctype html><meta charset="utf-8"><title>Rechnungsprüfung</title><div style="font-family:-apple-system,Segoe UI,Arial,sans-serif;max-width:560px;margin:40px auto;line-height:1.5">${inhalt}</div>` } }];"""

entscheidung_nodes = [
    node("Webhook: Entscheidung", "n8n-nodes-base.webhook", 2, [0, 0],
         {"httpMethod": "GET", "path": "entscheidung", "responseMode": "responseNode", "options": {}},
         webhookId="9b2e4c10-entscheidung-0000-000000000001"),
    http("Prüfdienst: Entscheidung speichern", [240, 0], "POST", "={{ $env.PRUEFDIENST_URL }}/api/entscheidung",
         "={{ JSON.stringify({ rechnung_id: $json.query.r, aktion: $json.query.a, token: $json.query.t, kommentar: $json.query.k || null }) }}",
         onError="continueRegularOutput"),
    code("Antwortseite", [480, 0], SEITE),
    wenn("SRW-Job abschließen?", [720, 0], "={{ $env.PRUEFMODUS === 'srw' && !!$json.srw_job_id && !!$json.entscheidung_id && $json.aktion !== 'vorschlag_falsch' }}"),
    http("SRW: Job freigeben", [960, -120], "POST", "={{ $env.SRW_API_URL }}/api/jobs/{{ $json.srw_job_id }}/approve",
         "={{ JSON.stringify({ notes: 'Entscheidung ' + $json.aktion + ' durch ' + ($json.person || 'unbekannt') + ' (Mail-Link)' }) }}",
         headers=SRW_AUTH, onError="continueRegularOutput",
         notes="Nur nötig, wenn der Expert mit autonomy=review läuft. Bei autonomy=full ist der Job schon abgeschlossen."),
    node("Seite anzeigen", "n8n-nodes-base.respondToWebhook", 1.1, [1200, 0], {
        "respondWith": "text", "responseBody": "={{ $('Antwortseite').item.json.html }}",
        "options": {"responseHeaders": {"entries": [{"name": "Content-Type", "value": "text/html; charset=utf-8"}]}}}),
]
entscheidung_conn = verbinde(
    ("Webhook: Entscheidung", "Prüfdienst: Entscheidung speichern"),
    ("Prüfdienst: Entscheidung speichern", "Antwortseite"),
    ("Antwortseite", "SRW-Job abschließen?"),
    ("SRW-Job abschließen?", "SRW: Job freigeben", 0),
    ("SRW-Job abschließen?", "Seite anzeigen", 1),
    ("SRW: Job freigeben", "Seite anzeigen"),
)


def workflow(wid, name, nodes, conn):
    return {"id": wid, "name": name, "nodes": nodes, "connections": conn, "active": True,
            "settings": {"executionOrder": "v1", "saveManualExecutions": True, "saveDataSuccessExecution": "all"},
            "pinData": {}, "tags": []}


OUT.mkdir(exist_ok=True)
for wid, name, n, c, datei in (
        ("Fall08Eingang0001", "Fall 08 – Rechnungseingang", eingang_nodes, eingang_conn, "01_rechnungseingang.json"),
        ("Fall08Entsch00002", "Fall 08 – Entscheidung aus Mail", entscheidung_nodes, entscheidung_conn, "02_entscheidung.json")):
    (OUT / datei).write_text(json.dumps(workflow(wid, name, n, c), ensure_ascii=False, indent=2), encoding="utf-8")
    print("geschrieben:", OUT / datei)
