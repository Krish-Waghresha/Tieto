"""Render the sticky PR comment (one screen collapsed) from the ledger only."""
from __future__ import annotations

import re

GRADE = {
    "PROVEN": ("✅", "proven"),
    "MEASURED": ("🧪", "measured"),
    "HEURISTIC": ("🔶", "heuristic"),
    "ARGUED": ("💬", "argued (AI)"),
    "ABSTAINED": ("✋", "AI abstained"),
    "UNSUPPORTED": ("⬜", "not run"),
}
TIER = {"LIGHT": "🟩 LIGHT", "STANDARD": "🟦 STANDARD", "DEEP": "🟧 DEEP"}
STATUS_ICON = {"CONFIRMED": "🧪 confirmed by test", "DISPROVED": "🧪 disproved by test", "NOT CONFIRMED": "🧪 not confirmed",
               "SUPPORTED BY FACTS, NOT EXECUTED": "💬 argued — supported by facts, test not run yet", "FACTS DO NOT HOLD": "❌ facts do not hold"}
MARKER = "<!-- dfr:sticky -->"


def g(grade: str) -> str:
    icon, word = GRADE.get(grade, ("•", grade.lower()))
    return f"{icon} {word}"


def md_escape(text: str) -> str:
    """Repo-derived text is data: neutralise HTML/markdown control that could inject UI or links."""
    text = str(text).replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\]\(", "]​(", text)  # break markdown links
    return text.replace("@", "@​")  # no accidental mentions


def mm(label: str) -> str:
    return '"' + str(label).replace('"', "#quot;").replace("`", "") + '"'


def link(ledger: dict, hunk_id: str, prefix: str) -> str:
    path, _, line = hunk_id.partition("#L")
    repo, head = ledger["pin"]["repo"], ledger["pin"]["head"]
    name = path.rsplit("/", 1)[-1]
    if not repo:
        return f"`{name}#L{line}`"
    return f"[`{name}#L{line}`](https://github.com/{repo}/blob/{head}/{prefix}{path}#L{line})"


def mermaid(ledger: dict) -> str:
    fan = next((f for f in ledger["facts"] if f["kind"] == "fanout"), None)
    br = next((f for f in ledger["facts"] if f["kind"] == "branch"), None)
    if not fan:
        return ""
    callers = mm(f"{len(fan['methods'])} methods · {fan['count']} call sites")
    lines = ["flowchart LR",
             "  subgraph B[Before]",
             f"    b1[{callers}] --> b2[{mm(fan['field'])}] --> b3[{mm('warning reported')}]",
             "  end",
             "  subgraph A[After]",
             f"    a1[{callers}] --> a2[{mm(fan['field'])}]"]
    if br:
        lines += [f"    a2 --> a3[{mm(br['method'])}]:::changed",
                  f"    a3 --> a4{{{mm('location in this compilation?')}}}:::changed",
                  f"    a4 -- yes --> a5[{mm('warning reported')}]",
                  f"    a4 -- no --> a6[{mm('dropped: no warning')}]:::risk"]
    lines += ["  end",
              "  classDef changed stroke-width:3px,stroke-dasharray:5 3",
              "  classDef risk stroke-width:3px"]
    return "\n".join(lines)


def render(ledger: dict, report_url: str = "", prefix: str = "") -> str:
    t = ledger["triage"]
    n_open = len(ledger["open_items"])
    proofs = ledger["proofs"]
    ran = [p for p in proofs if p.get("status") == "executed"]
    failing_expectation = [p for p in ran if p["result"] == "VIOLATED"]
    if failing_expectation:
        verdict = f"⛔ {len(failing_expectation)} expected result(s) violated"
    elif n_open:
        dep = len(ledger.get("dependent_items", []))
        verdict = f"⚠️ Needs your decision on **{n_open}** items" + (f" (+{dep} that follow from them)" if dep else "")
    else:
        verdict = "✅ No decisions need you"
    head = ledger["pin"]["head"][:7]
    rules = ", ".join(f"`{f['rule']}`" for f in t["fired"] if f["tier"] in ("DEEP", "STANDARD"))
    cov = ledger["coverage"]
    cov_txt = "✅ every changed hunk explained" if cov["complete"] else f"❌ {len(cov['unexplained'])} hunk(s) unexplained"
    tests_txt = (f"proofs run {len(ran)}/{len(proofs)}" if ran else f"⬜ proofs not run yet (0/{len(proofs)})")

    out = [MARKER, f"### {TIER[t['tier']]} review · {verdict}",
           f"Requirement **{ledger['requirement']['id']}** · head `{head}` · {len(ledger['files'])} files · rules {rules} · {tests_txt} · {cov_txt}",
           ""]

    if ledger["scope"]:
        s = next((x for x in ledger["scope"] if x["mismatch"]), None)
        if s:
            out += [f"> **Scope check:** {md_escape(s['text'])}", ""]

    out += ["**What to do**"]
    for i, w in enumerate(ledger["what_to_do"], 1):
        out.append(f"{i}. {md_escape(w['text'])}")
    sign_hint = "Open the full report, answer the 3 quick questions, use **Sign** to generate a `/sign` text, and submit it as a PR review (Request changes / Approve)."
    out.append(f"{len(ledger['what_to_do']) + 1}. {sign_hint}" + (f" → [full report]({report_url})" if report_url else ""))
    out.append("")

    # evidence row
    order = ["PROVEN", "MEASURED", "HEURISTIC", "ARGUED", "ABSTAINED", "UNSUPPORTED"]
    c = ledger["grade_counts"]
    out += ["| " + " | ".join(g(k) for k in order) + " |", "|" + ":-:|" * len(order),
            "| " + " | ".join(str(c.get(k, 0)) for k in order) + " |", ""]

    # decision cards
    for d in ledger["decisions"]:
        ev = ", ".join(f"{g('MEASURED') if p.get('status') == 'executed' else g('UNSUPPORTED')} {p['id']}" for p in d.get("evidence", [])) or "—"
        where = " · ".join(link(ledger, c, prefix) for c in d["claims"][:2])
        out += [f"<details><summary><b>{d['id']} · {md_escape(d['title'])}</b> · {g('ARGUED')} · {where}</summary>", "",
                f"**Before:** {md_escape(d['before'])}  ",
                f"**After:** {md_escape(d['after'])}  ",
                f"**Why (agent):** {md_escape(d['rationale'])}  ",
                f"**Requirement:** {md_escape(d['trace']['status'])}{(' → ' + ', '.join(d['trace']['to'])) if d['trace']['to'] else ''}  ",
                f"**Could break / rollout:** {md_escape(d['dimensions']['rollout_safety'])}  ",
                f"**Evidence:** {ev}  ",
                f"**Alternatives:** {md_escape('; '.join(d['alternatives']))}",
                "", "</details>", ""]
    for f in ledger["findings"]:
        out += [f"<details><summary><b>{f['id']} · {md_escape(f['title'])}</b> · {STATUS_ICON.get(f['status'], f['status'])}</summary>", "",
                md_escape(f["argument"]), "",
                "**Deterministic facts:** " + "; ".join(
                    f"{'✅' if x['holds'] else '❌'} {md_escape(x['text'])}" for x in ledger["facts"] if x["id"] in f["facts"]), "",
                "**Probes:** " + "; ".join(f"{p['id']}: {p.get('note', '')}" for p in f["evidence"]), "",
                f"**Fix hint:** {md_escape(f['fix_hint'])}", "", "</details>", ""]
    for a in ledger["abstentions"]:
        out += [f"<details><summary><b>{a['id']} · {md_escape(a['title'])}</b> · {g(a['grade'])}</summary>", "",
                f"**Why:** {md_escape(a['why'])}  ", f"**You decide:** {md_escape(a['human_action'])}", "", "</details>", ""]

    mer = mermaid(ledger)
    if mer and t["tier"] != "LIGHT":
        out += ["<details><summary>Change graph (before → after) · 🔶 heuristic, text-level parse</summary>", "",
                "```mermaid", mer, "```", "", "</details>", ""]

    out += ["**⬜ Not checked:** " + md_escape("; ".join(ledger["not_checked"])), ""]
    out += [f"<sub>Decision-First Review demo · tier and facts are deterministic · decision cards are AI-argued (simulated extractor in this demo) · "
            f"ledger `{ledger['ledger_sha256'][:12]}` · the AI never approves; a named human signs.</sub>"]
    return "\n".join(out)
