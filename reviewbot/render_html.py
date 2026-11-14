"""Render the single-file HTML review report from the ledger only.

Security: every repo-derived string is HTML-escaped; one inline script and one inline style are allowed
by sha256 hash in the CSP (no 'unsafe-inline', no external loads). The ledger is embedded as inert JSON.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
from pathlib import Path

from .render_md import GRADE, TIER, STATUS_ICON

STATIC = Path(__file__).parent / "static"
GRADE_CLASS = {"PROVEN": "g-proven", "MEASURED": "g-measured", "HEURISTIC": "g-heur", "ARGUED": "g-argued",
               "ABSTAINED": "g-abst", "UNSUPPORTED": "g-unsup"}


def e(x) -> str:
    return html.escape(str(x), quote=True)


def chip(grade: str) -> str:
    icon, word = GRADE.get(grade, ("•", grade))
    return f'<span class="chip {GRADE_CLASS.get(grade, "")}">{icon} {e(word)}</span>'


def csp_hash(text: str) -> str:
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"


def grade_bar(counts: dict) -> str:
    order = ["PROVEN", "MEASURED", "HEURISTIC", "ARGUED", "ABSTAINED", "UNSUPPORTED"]
    total = sum(counts.get(k, 0) for k in order) or 1
    x, parts, legend = 0.0, [], []
    for k in order:
        n = counts.get(k, 0)
        if not n:
            continue
        w = 600 * n / total
        parts.append(f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="28" class="{GRADE_CLASS[k]}-fill"><title>{k}: {n}</title></rect>'
                     f'<text x="{x + w / 2:.1f}" y="19" text-anchor="middle" class="barlabel">{n}</text>')
        x += w
        legend.append(f"<li>{chip(k)} {n}</li>")
    return (f'<svg viewBox="0 0 600 28" class="bar" role="img" aria-label="Evidence by grade">{"".join(parts)}</svg>'
            f'<ul class="legend">{"".join(legend)}</ul>')


def node(x, y, w, h, label, cls="") -> str:
    return (f'<g class="node {cls}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8"/>'
            f'<text x="{x + w / 2}" y="{y + h / 2 + 5}" text-anchor="middle">{e(label)}</text></g>')


def arrow(x1, y1, x2, y2, label="") -> str:
    lab = f'<text x="{(x1 + x2) / 2}" y="{(y1 + y2) / 2 - 6}" text-anchor="middle" class="elabel">{e(label)}</text>' if label else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="edge" marker-end="url(#arr)"/>{lab}'


def graph_svg(ledger: dict) -> str:
    fan = next((f for f in ledger["facts"] if f["kind"] == "fanout"), None)
    br = next((f for f in ledger["facts"] if f["kind"] == "branch"), None)
    if not fan:
        return "<p>No graph: no cross-cutting change detected.</p>"
    callers = f"{len(fan['methods'])} methods · {fan['count']} call sites"
    s = ['<svg viewBox="0 0 980 300" class="graph" role="img" aria-label="Before and after flow">',
         '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0L10,5L0,10z"/></marker></defs>',
         '<text x="10" y="22" class="lane">BEFORE</text>',
         node(10, 35, 200, 44, callers), arrow(210, 57, 260, 57), node(260, 35, 170, 44, fan["field"]),
         arrow(430, 57, 480, 57), node(480, 35, 170, 44, "warning reported", "ok"),
         '<text x="10" y="132" class="lane">AFTER</text>',
         node(10, 145, 200, 44, callers), arrow(210, 167, 260, 167), node(260, 145, 170, 44, fan["field"])]
    if br:
        s += [arrow(430, 167, 470, 167), node(470, 145, 220, 44, br["method"], "changed"),
              arrow(690, 167, 730, 167), node(730, 145, 230, 44, "location in this compilation?", "changed"),
              arrow(845, 189, 845, 225, "yes"), node(760, 225, 170, 40, "warning reported", "ok"),
              arrow(730, 180, 600, 245, "no"), node(420, 225, 180, 40, "DROPPED — no warning", "risk")]
    s.append("</svg>")
    return "".join(s)


def audio_script(ledger: dict) -> str:
    t = ledger["triage"]
    d1 = ledger["decisions"][0] if ledger["decisions"] else None
    parts = [
        "This briefing is synthesized from the review ledger. It is not evidence.",
        f"Requirement {ledger['requirement']['id']}. The change was routed to {t['tier'].lower()} review because "
        + ", ".join(f["detail"] for f in t["fired"] if f["tier"] == "DEEP") + ".",
    ]
    if d1:
        parts.append(f"The main decision: {d1['title']}. Before: {d1['before']} After: {d1['after']}")
    for s in ledger["scope"]:
        if s["mismatch"]:
            parts.append(s["text"])
    for f in ledger["findings"]:
        parts.append(f"One finding: {f['title']}. Status: {f['status'].lower()}.")
    for a in ledger["abstentions"]:
        parts.append(f"The AI did not decide: {a['title']}.")
    parts.append("You decide. Open the decisions, answer the three questions, and sign.")
    return " ".join(p.replace("`", "") for p in parts)


def render(ledger: dict, prefix: str = "") -> str:
    css = (STATIC / "report.css").read_text()
    js = (STATIC / "report.js").read_text()
    t = ledger["triage"]
    pin = ledger["pin"]
    repo, head = pin["repo"], pin["head"]

    def src_link(hid: str) -> str:
        path, _, line = hid.partition("#L")
        label = f"{path.rsplit('/', 1)[-1]}#L{line}"
        if repo:
            return f'<a href="https://github.com/{e(repo)}/blob/{e(head)}/{e(prefix + path)}#L{e(line)}" rel="noopener">{e(label)}</a>'
        return f"<code>{e(label)}</code>"

    n_open = len(ledger["open_items"])
    verdict = f"Needs your decision on {n_open} items" if n_open else "No decisions need you"
    H = []
    H.append(f'<header><div class="demo">DEMO · reference implementation, not a product · decision extraction simulated</div>'
             f'<h1><span class="tier tier-{e(t["tier"])}">{e(TIER[t["tier"]])}</span> {e(verdict)}</h1>'
             f'<p class="pin">Requirement <b>{e(ledger["requirement"]["id"])}</b> · PR #{e(pin.get("pr"))} · base <code>{e(pin["base"][:7])}</code> → head <code>{e(head[:7])}</code>'
             f' · upstream <code>{e(pin.get("upstream", {}).get("head_sha", "")[:7])}</code> · ledger <code>{e(ledger["ledger_sha256"][:12])}</code></p></header>')

    H.append('<nav>' + " ".join(f'<a href="#{a}">{b}</a>' for a, b in [
        ("todo", "What to do"), ("why", "Why this tier"), ("graph", "Graph"), ("decisions", "Decisions"),
        ("evidence", "Evidence"), ("coverage", "Coverage"), ("quiz", "Quiz"), ("audio", "Listen"), ("sign", "Sign")]) + "</nav>")

    # what to do + glance
    H.append('<section id="todo"><h2>What to do</h2><ol class="todo">')
    for w in ledger["what_to_do"]:
        H.append(f"<li>{e(w['text'])} " + " ".join(f'<a href="#{e(r)}" class="ref">{e(r)}</a>' for r in w["refs"]) + "</li>")
    H.append('<li>Answer the <a href="#quiz">3 quick questions</a>, then <a href="#sign">sign</a>.</li></ol>')
    H.append(f'<h3>Evidence at a glance</h3>{grade_bar(ledger["grade_counts"])}')
    for s in ledger["scope"]:
        if s["mismatch"]:
            H.append(f'<p class="callout risk">⚠ Scope check ({chip(s["grade"])}): {e(s["text"])}</p>')
    H.append("</section>")

    # why tier
    H.append('<section id="why"><h2>Why this tier</h2><p>The tier is computed by plain, unit-tested code from <code>review-policy.json</code> '
             '(base revision). AI output cannot lower it. Every rule cites the incident or regulation behind it.</p>'
             '<table><tr><th>Rule</th><th>Tier</th><th>Where</th><th>What fired</th><th>Why the rule exists</th></tr>')
    for f in t["fired"]:
        H.append(f'<tr><td><code>{e(f["rule"])}</code></td><td>{e(f["tier"] or "check")}</td><td>{e(", ".join(f["where"][:4]))}</td>'
                 f'<td>{e(f["detail"])} {chip(f["grade"])}</td><td>{e(f["why"])}<br><small>{e(f["motivated_by"])}</small></td></tr>')
    for r in t["required_checks"]:
        H.append(f'<tr><td><code>{e(r["rule"])}</code></td><td>required check</td><td>{e(len(r["files"]))} test file(s)</td>'
                 f'<td>{e(r["check"])}</td><td>{e(r["why"])}<br><small>{e(r["motivated_by"])}</small></td></tr>')
    H.append("</table></section>")

    # graph
    H.append(f'<section id="graph"><h2>What changed in the flow</h2><p>Built by a deterministic text-level parser {chip("HEURISTIC")} '
             f'(Roslyn ControlFlowGraph proposed for production). Dashed = new code. Only the changed part is shown.</p>{graph_svg(ledger)}</section>')

    # decisions
    H.append('<section id="decisions"><h2>Decisions the agent made</h2><p>Each card is <b>AI-argued</b> (simulated extractor in this demo) '
             'and cites changed lines. Give your verdict first; the bot\'s recommendation is revealed after (anti-anchoring).</p>')
    for d in ledger["decisions"]:
        dims = "".join(f"<tr><th>{e(k.replace('_', ' '))}</th><td>{e(v)}</td></tr>" for k, v in d["dimensions"].items())
        ev = " ".join(f'<a class="ref" href="#{e(p["id"])}">{e(p["id"])}</a>' for p in d.get("evidence", [])) or "—"
        H.append(f'''<article class="card" id="{e(d["id"])}">
<h3>{e(d["id"])} · {e(d["title"])} {chip("ARGUED")}</h3>
<p class="where">{" · ".join(src_link(c) for c in d["claims"])}</p>
<div class="ba"><div class="before"><h4>Before</h4><p>{e(d["before"])}</p></div><div class="after"><h4>After</h4><p>{e(d["after"])}</p></div></div>
<p><b>Why (agent):</b> {e(d["rationale"])} · <b>Requirement:</b> {e(d["trace"]["status"])} {e(", ".join(d["trace"]["to"]))}</p>
<table class="dims">{dims}</table>
<p><b>Alternatives:</b> {e("; ".join(d["alternatives"]))} · <b>Evidence:</b> {ev}</p>
<fieldset class="verdict" data-id="{e(d["id"])}"><legend>Your verdict on {e(d["id"])}</legend>
<label><input type="radio" name="v-{e(d["id"])}" value="accept"> accept</label>
<label><input type="radio" name="v-{e(d["id"])}" value="request_change"> request change</label>
<label><input type="radio" name="v-{e(d["id"])}" value="reject"> reject</label></fieldset>
<details class="rec"><summary>Bot recommendation (open after your verdict)</summary><p><b>{e(d["recommended"])}</b> — {e(d["recommendation_reason"])}</p></details>
</article>''')
    for f in ledger["findings"]:
        facts = "".join(f'<li>{"✅" if x["holds"] else "❌"} {e(x["text"])} {chip(x["grade"])} <small>lines {e(x["lines"][:5])}</small></li>'
                        for x in ledger["facts"] if x["id"] in f["facts"])
        probes = "".join(f'<li><a class="ref" href="#{e(p["id"])}">{e(p["id"])}</a> {e(p["title"])}: <b>{e(p.get("result"))}</b> — {e(p.get("note", ""))}</li>' for p in f["evidence"])
        H.append(f'''<article class="card finding" id="{e(f["id"])}">
<h3>{e(f["id"])} · {e(f["title"])} <span class="status">{e(STATUS_ICON.get(f["status"], f["status"]))}</span></h3>
<p class="where">{" · ".join(src_link(c) for c in f["claims"])}</p>
<p>{e(f["argument"])}</p><h4>Deterministic facts</h4><ul>{facts}</ul><h4>Probes (disprove-it)</h4><ul>{probes}</ul>
<p><b>Fix hint:</b> {e(f["fix_hint"])}</p>
<fieldset class="verdict" data-id="{e(f["id"])}"><legend>Is {e(f["id"])} valid?</legend>
<label><input type="radio" name="v-{e(f["id"])}" value="valid"> valid</label>
<label><input type="radio" name="v-{e(f["id"])}" value="invalid"> not valid</label></fieldset></article>''')
    for a in ledger["abstentions"]:
        H.append(f'''<article class="card abst" id="{e(a["id"])}"><h3>{e(a["id"])} · {e(a["title"])} {chip(a["grade"])}</h3>
<p><b>Why the AI did not decide:</b> {e(a["why"])}</p><p><b>You decide:</b> {e(a["human_action"])}</p>
<fieldset class="verdict" data-id="{e(a["id"])}"><legend>Resolution for {e(a["id"])}</legend>
<label><input type="radio" name="v-{e(a["id"])}" value="resolved"> resolved</label>
<label><input type="radio" name="v-{e(a["id"])}" value="accept_risk"> accept as residual risk</label>
<label><input type="radio" name="v-{e(a["id"])}" value="defer"> defer to owner/maintainers</label></fieldset></article>''')
    H.append("</section>")

    # evidence
    H.append('<section id="evidence"><h2>Evidence ledger</h2><h3>Proofs (executed checks)</h3>'
             '<table><tr><th>ID</th><th>Check</th><th>Status</th><th>Result</th><th>Detail</th></tr>')
    for p in ledger["proofs"]:
        st = "executed" if p.get("status") == "executed" else "not executed here"
        g = p["grade"] if p.get("status") == "executed" else "UNSUPPORTED"
        det = e(p.get("note", ""))
        if p.get("command"):
            det += f'<br><small><code>{e(p["command"])}</code> · SDK {e(p.get("sdk"))} · upstream <code>{e(str(p.get("upstream_rev"))[:7])}</code></small>'
        if p.get("log_url"):
            det += f' · <a href="{e(p["log_url"])}" rel="noopener">CI log</a>'
        for tt in p.get("tests", [])[:3]:
            det += f'<details><summary>{e(tt["name"])}: {e(tt["outcome"])}</summary><pre>{e(tt["message"][:900])}</pre></details>'
        H.append(f'<tr id="{e(p["id"])}"><td>{e(p["id"])}</td><td>{e(p["title"])}{("<br><small>" + e(p["limit"]) + "</small>") if p.get("limit") else ""}</td>'
                 f'<td>{chip(g)} {e(st)}</td><td><b>{e(p.get("result"))}</b></td><td>{det}</td></tr>')
    H.append('</table><h3>Facts (deterministic)</h3><table><tr><th>ID</th><th>Fact</th><th>Grade</th><th>Holds</th><th>Lines</th></tr>')
    for f in ledger["facts"]:
        H.append(f'<tr><td><code>{e(f["id"])}</code></td><td>{e(f["text"])}<br><small>{e(f.get("grade_note", ""))}</small></td>'
                 f'<td>{chip(f["grade"])}</td><td>{e({True: "yes", False: "no", None: "—"}[f.get("holds")])}</td><td>{e(str(f.get("lines", ""))[:60])}</td></tr>')
    H.append("</table></section>")

    # coverage
    H.append('<section id="coverage"><h2>Coverage — is every change explained?</h2><table><tr><th>Hunk</th><th>+/−</th><th>Explained by</th></tr>')
    for h in ledger["coverage"]["hunks"]:
        cb = " ".join(f'<a class="ref" href="#{e(x)}">{e(x)}</a>' for x in h["claimed_by"]) or '<b class="bad">UNEXPLAINED</b>'
        H.append(f'<tr><td>{src_link(h["id"])}</td><td>+{h["added"]} / −{h["removed"]}</td><td>{cb}</td></tr>')
    status = "✅ every changed hunk is claimed by a decision, finding or fact" if ledger["coverage"]["complete"] else "❌ unexplained changes raise the tier"
    H.append(f'</table><p>{status}</p><h3>Not checked</h3><ul>' + "".join(f"<li>{e(x)}</li>" for x in ledger["not_checked"]) + "</ul></section>")

    # quiz
    H.append('<section id="quiz"><h2>Quick check (3 questions, does not block merge)</h2>'
             '<p>Answer keys come from deterministic facts or executed probes, never from the AI. Your score goes into the signed record.</p><form id="quizform">')
    for q in ledger["quiz"]:
        H.append(f'<fieldset class="q" data-id="{e(q["id"])}" data-answer="{e(q.get("answer", ""))}"><legend>{e(q["id"])}. {e(q["question"])}</legend>')
        if q["kind"] == "free":
            H.append(f'<textarea name="{e(q["id"])}" rows="2" maxlength="400"></textarea>')
        else:
            for i, o in enumerate(q.get("options", [])):
                label = o.rsplit("/", 1)[-1] if q["kind"] == "line" else o
                H.append(f'<label><input type="radio" name="{e(q["id"])}" value="{i}"> {e(label)}</label>')
            H.append(f'<p class="explain" hidden>Key {chip(q.get("key_grade", "ARGUED"))}: {e(q.get("explain", ""))} {e(q.get("key_note", ""))}</p>')
        H.append("</fieldset>")
    H.append('<button type="button" id="quizcheck">Check answers</button> <span id="quizscore" aria-live="polite"></span></form></section>')

    # audio
    script = audio_script(ledger)
    H.append(f'<section id="audio"><h2>Listen (≈1 min)</h2><p class="callout">Synthesized from the ledger by template — <b>not evidence</b>. '
             f'Uses your browser\'s speech engine; nothing is uploaded.</p><button type="button" id="play">▶ Play briefing</button> '
             f'<button type="button" id="stop">■ Stop</button><details><summary>Transcript</summary><p id="audiotext">{e(script)}</p></details></section>')

    # sign
    H.append(f'''<section id="sign"><h2>Sign</h2><p>Your verdicts above are collected into a <code>/sign</code> text. On the PR, open <b>Files changed → Review changes</b>,
paste it, and submit as <b>Request changes</b> or <b>Approve</b> (matching your decision). The bot checks the head SHA, the ledger, that every item is resolved,
that the review state matches, and that the signer is not the PR author, then sets the <code>decision-record</code> status.
The AI never signs and never counts as a reviewer.</p>
<label>Decision <select id="decision"><option value="request_changes">request changes</option><option value="approve">approve</option><option value="reject">reject</option></select></label>
<label class="block">Residual risk you accept <textarea id="risk" rows="2" maxlength="500"></textarea></label>
<button type="button" id="gensign">Generate /sign text</button> <button type="button" id="copysign">Copy</button>
<pre id="signout" aria-live="polite">(enable JavaScript to generate)</pre></section>''')

    data = json.dumps({"head": head, "ledger": ledger["ledger_sha256"][:12],
                       "items": [d["id"] for d in ledger["decisions"]] + [f["id"] for f in ledger["findings"]] + [a["id"] for a in ledger["abstentions"]],
                       "audio": script}).replace("</", "<\\/")
    csp = f"default-src 'none'; img-src data:; style-src {csp_hash(css)}; script-src {csp_hash(js)}; base-uri 'none'; form-action 'none'"
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta http-equiv="Content-Security-Policy" content="{csp}">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{e(ledger["requirement"]["id"])} · Decision-First Review</title><style>{css}</style></head><body>'
            + "".join(H)
            + f'<footer>Decision-First Review demo · ledger <code>{e(ledger["ledger_sha256"])}</code> · generated from the ledger only.</footer>'
            + f'<script type="application/json" id="data">{data}</script><script>{js}</script></body></html>')
