"""Render the sticky PR comment (one screen when collapsed) and the full markdown report from the ledger only."""
from __future__ import annotations

import re

# Plain-language labels (judge feedback: no internal jargon in what reviewers read)
GRADE = {
    "PROVEN": ("✅", "checked by tool"),
    "MEASURED": ("🧪", "test result"),
    "HEURISTIC": ("🔶", "tool estimate"),
    "ARGUED": ("💬", "AI reasoning, unverified"),
    "ABSTAINED": ("✋", "AI won't decide"),
    "UNSUPPORTED": ("⬜", "not run"),
}
TIER = {"LIGHT": "🟩 Light check", "STANDARD": "🟦 Normal review", "DEEP": "🟧 Deep review"}
RESULT = {"HOLDS": "✅ holds", "VIOLATED": "❌ violated", "OBSERVED": "👁 observed", "UNSUPPORTED": "⬜ not run"}
STATUS_ICON = {"CONFIRMED": "🧪 confirmed by a test", "DISPROVED": "🧪 disproved by a test", "NOT CONFIRMED": "🧪 test did not confirm it",
               "SUPPORTED BY FACTS, NOT EXECUTED": "💬 AI reasoning backed by tool facts — test not run yet", "FACTS DO NOT HOLD": "❌ facts do not hold"}
MARKER = "<!-- dfr:sticky -->"


def g(grade: str) -> str:
    icon, word = GRADE.get(grade, ("•", grade.lower()))
    return f"{icon} {word}"


def md_escape(text) -> str:
    """Repo-derived text is data: neutralise HTML, links, mentions, issue refs, code fences and line breaks."""
    text = " ".join(str(text).split())  # no newlines → no reference-link definitions or block breakouts
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("[", "&#91;").replace("]", "&#93;")  # no inline or reference links
    text = re.sub(r"(?i)\b(https?|ftp|www)", lambda m: m.group(1)[0] + "​" + m.group(1)[1:], text)  # no autolinks
    text = text.replace("@", "@​").replace("#", "#​")  # no mentions or issue refs
    return text


def code(text) -> str:
    """Inline code span that cannot be broken out of."""
    t = " ".join(str(text).split()).replace("`", "ˋ")
    return f"`{t}`"


def mm(label) -> str:
    return '"' + re.sub(r"[^\w .·:?,()\-]", "", str(label)) + '"'


def link(ledger: dict, hunk_id: str) -> str:
    path, _, line = hunk_id.partition("#L")
    repo, head = ledger["pin"]["repo"], ledger["pin"]["head"]
    f = next((x for x in ledger["files"] if x["path"] == path), None)
    repo_path = f["repo_path"] if f else path
    name = path.rsplit("/", 1)[-1]
    if not repo or not re.fullmatch(r"[\w./\-]+", repo_path) or not line.isdigit():
        return code(f"{name}#L{line}")
    return f"[{code(f'{name}:{line}')}](https://github.com/{repo}/blob/{head}/{repo_path}#L{line})"


def mermaid(ledger: dict) -> str:
    fan = next((f for f in ledger["facts"] if f["kind"] == "fanout"), None)
    br = next((f for f in ledger["facts"] if f["kind"] == "branch"), None)
    if not fan:
        return ""
    callers = mm(f"{len(fan['methods'])} methods · {fan['count']} call sites")
    lines = ["flowchart LR",
             "  subgraph B[Before]",
             f"    b1[{callers}] --> b2[{mm(fan['field'])}] --> b3[{mm('warning shown to user')}]",
             "  end",
             "  subgraph A[After]",
             f"    a1[{callers}] --> a2[{mm(fan['field'])}]"]
    if br:
        lines += [f"    a2 --> a3[{mm(br['method'])}]:::changed",
                  f"    a3 --> a4{{{mm('location in this project?')}}}:::changed",
                  f"    a4 -- yes --> a5[{mm('warning shown to user')}]",
                  f"    a4 -- no --> a6[{mm('dropped: no warning')}]:::risk"]
    lines += ["  end",
              "  classDef changed stroke-width:3px,stroke-dasharray:5 3",
              "  classDef risk stroke-width:3px"]
    return "\n".join(lines)


def checks_line(ledger: dict) -> str:
    proofs = ledger["proofs"]
    ran = [p for p in proofs if p.get("status") == "executed"]
    if not ran:
        return f"**Checks run: 0 of {len(proofs)}** ⬜ — nothing has been executed yet; everything below is tool facts and AI reasoning."
    bad = [p["id"] for p in ran if p["result"] == "VIOLATED"]
    return f"**Checks run: {len(ran)} of {len(proofs)}**" + (f" · ❌ violated: {', '.join(bad)}" if bad else " · none violated")


def owner_of(ledger: dict) -> str:
    owners = ledger.get("owners") or []
    return owners[0]["owner"] if owners else "a named area owner"


def render(ledger: dict, report_url: str = "", prefix: str = "", full: bool = False) -> str:
    t = ledger["triage"]
    n_open = len(ledger["open_items"])
    verdict = f"⚠️ Needs your decision on **{n_open}** items" if n_open else "✅ No decisions need you"
    s = ledger.get("summary") or {}
    out = [MARKER, f"### {TIER[t['tier']]} · {verdict}", ""]
    if s:
        out += [f"**What this PR does:** {md_escape(s.get('what', ''))}", "",
                f"**Bot's read:** {md_escape(s.get('verdict', ''))}", ""]
    out += [f"**Who decides:** {code(owner_of(ledger))} (area owner) — not the PR author, not the AI. The AI never approves.", "",
            checks_line(ledger), ""]
    for sc in ledger["scope"]:
        if sc["mismatch"]:
            out += [f"> **Scope check** ({g(sc['grade'])}): {md_escape(sc['text'])}", ""]

    out += ["**What to do**"]
    for i, w in enumerate(ledger["what_to_do"], 1):
        out.append(f"{i}. {md_escape(w['text'])}")
    last = ("Open the full report" + (f" → **[report]({report_url})**" if report_url else "") +
            ", answer 3 quick questions, press **Sign**, and submit the generated text as a PR review (*Request changes* or *Approve*).")
    out += [f"{len(ledger['what_to_do']) + 1}. {last}", ""]

    ac, trace = ledger["requirement"].get("acceptance_criteria", {}), ledger["requirement"].get("trace", {})
    if ac:
        res = {p["id"]: p for p in ledger["proofs"]}
        rows = ["| Requirement | Covered by | Checks |", "|---|---|---|"]
        for k, v in ac.items():
            tr = trace.get(k, {})
            chk = ", ".join(f"{p} {RESULT.get(res.get(p, {}).get('result'), '⬜ not run')}" for p in tr.get("proofs", [])) or "—"
            rows.append(f"| **{k}** {md_escape(v)} | {', '.join(tr.get('by', [])) or '⚠️ no decision'} | {chk} |")
        out += ["<details><summary>Requirement " + code(ledger["requirement"]["id"]) + " → decisions → checks</summary>", "", *rows, "",
                md_escape(trace.get("AC3", {}).get("note", "")), "", "</details>", ""]

    children = {}
    for d in ledger["decisions"]:
        r = str(d.get("recommended", ""))
        if r.startswith("follow_"):
            children.setdefault(r[len("follow_"):], []).append(d)
    for d in ledger["decisions"]:
        if str(d.get("recommended", "")).startswith("follow_"):
            continue
        ev = ", ".join(f"{p['id']} {RESULT.get(p.get('result'), '⬜ not run')}" for p in d.get("evidence", [])) or "none yet"
        out += [f"<details><summary><b>{d['id']} · {md_escape(d['title'])}</b> · {g('ARGUED')}</summary>", "",
                f"**Where:** {' · '.join(link(ledger, c) for c in d['claims'])}  ",
                f"**Before:** {md_escape(d['before'])}  ",
                f"**After:** {md_escape(d['after'])}  ",
                f"**Why (agent):** {md_escape(d['rationale'])}  ",
                f"**Requirement:** {md_escape(d['trace']['status'])}{(' → ' + ', '.join(d['trace']['to'])) if d['trace']['to'] else ''}  ",
                f"**If wrong:** {md_escape(d['dimensions']['rollout_safety'])}  ",
                f"**Checks:** {ev}  ",
                f"**Alternatives:** {md_escape('; '.join(d['alternatives']))}"]
        for c in children.get(d["id"], []):
            out.append(f"  \n↳ **{c['id']} follows {d['id']}:** {md_escape(c['title'])} ({' · '.join(link(ledger, x) for x in c['claims'])})")
        out += ["", "</details>", ""]
    for f in ledger["findings"]:
        out += [f"<details><summary><b>{f['id']} · AI finding: {md_escape(f['title'])}</b> · {STATUS_ICON.get(f['status'], f['status'])}</summary>", "",
                f"**Where:** {' · '.join(link(ledger, c) for c in f['claims'])}  ",
                md_escape(f["argument"]), "",
                "**Tool facts behind it:** " + "; ".join(
                    f"{'✅' if x.get('holds') else '❌'} {md_escape(x['text'])}" for x in ledger["facts"] if x["id"] in f["facts"]), "",
                "**Tests that try to disprove it:** " + "; ".join(
                    f"{p['id']} {md_escape(p['title'])} — {RESULT.get(p.get('result'), '')} {md_escape(p.get('note', ''))}" for p in f["evidence"]), "",
                f"**Fix hint:** {md_escape(f['fix_hint'])}", "", "</details>", ""]
    for a in ledger["abstentions"]:
        label = "AI won't decide" if a["grade"] == "ABSTAINED" else "Not checked — needs your call"
        out += [f"<details><summary><b>{a['id']} · {label}: {md_escape(a['title'])}</b></summary>", "",
                f"**Why:** {md_escape(a['why'])}  ", f"**You decide:** {md_escape(a['human_action'])}", "", "</details>", ""]

    mer = mermaid(ledger)
    if mer and t["tier"] != "LIGHT":
        out += ["<details><summary>Flow before → after (🔶 tool estimate from a text-level parse)</summary>", "",
                "```mermaid", mer, "```", "", "</details>", ""]

    rules = "; ".join(f"{code(f['rule'])} {md_escape(f['detail'])}" for f in t["fired"] if f["tier"] in ("DEEP", "STANDARD"))
    cov = ledger["coverage"]
    cov_txt = ("every changed block is assigned to a card or a tool fact (assignment by the simulated extractor)" if cov["complete"]
               else f"❌ {len(cov['unexplained'])} changed block(s) not explained by anything — tier raised")
    out += [f"<details><summary>Why {TIER[t['tier']]}, coverage, what was not checked</summary>", "",
            f"**Why this tier:** {rules}  ", f"**Coverage:** {cov_txt}  ",
            "**Not checked:** " + md_escape("; ".join(ledger["not_checked"])), "", "</details>", ""]

    if full:
        out += full_sections(ledger)
    out += [f"<sub>Decision-First Review (demo, not a product) · tier and facts computed by plain code from the base-revision policy · "
            f"decision cards are AI reasoning (simulated extractor in this demo) · evidence record {code(ledger['ledger_sha256'][:12])}</sub>"]
    return "\n".join(out)


def full_sections(ledger: dict) -> list[str]:
    """Extra sections for the rendered markdown report (used when no HTML hosting is available)."""
    out = ["---", "## Checks", "", "| ID | Check | Result | Detail |", "|---|---|---|---|"]
    for p in ledger["proofs"]:
        out.append(f"| {p['id']} | {md_escape(p['title'])} | {RESULT.get(p.get('result'), p.get('result'))} | {md_escape(p.get('note', ''))} |")
    out += ["", "## Tool facts", "", "| Fact | Kind | Holds |", "|---|---|---|"]
    for f in ledger["facts"]:
        holds = {True: "yes", False: "no", None: "n/a (measurement)"}[f.get("holds")]
        out.append(f"| {md_escape(f['text'])} | {g(f['grade'])} | {holds} |")
    out += ["", "## Changed blocks and what explains them", "", "| Block | +/− | Explained by |", "|---|---|---|"]
    for h in ledger["coverage"]["hunks"]:
        out.append(f"| {link(ledger, h['id'])} | +{h['added']}/−{h['removed']} | {', '.join(h['claimed_by']) or '❌ nothing'} |")
    out += ["", "## Quick check (answers in the folds)", ""]
    for q in ledger["quiz"]:
        out.append(f"**{q['id']}. {md_escape(q['question'])}**")
        if q.get("options"):
            for i, o in enumerate(q["options"]):
                out.append(f"- {chr(65 + i)}) {md_escape(o.rsplit('/', 1)[-1])}")
            ans = q["options"][q["answer"]].rsplit("/", 1)[-1] if isinstance(q.get("answer"), int) else "?"
            out += ["", f"<details><summary>Answer</summary>{md_escape(ans)} — {g(q.get('key_grade', 'ARGUED'))}: {md_escape(q.get('explain', ''))}</details>", ""]
        else:
            out += ["_Free text — write it in your /sign review as `could_break:`_", ""]
    items = [d["id"] for d in ledger["decisions"] if not str(d.get("recommended", "")).startswith("follow_")] + \
            [f["id"] for f in ledger["findings"]] + [a["id"] for a in ledger["abstentions"]]
    tmpl = ["/sign", f"head: {ledger['pin']['head']}", f"ledger: {ledger['ledger_sha256'][:12]}", "decision: request_changes"]
    tmpl += [f"{i}: " + ("accept|request_change|reject" if i.startswith("D") else "valid|invalid" if i.startswith("F") else "resolved|accept_risk|defer")
             for i in items]
    tmpl += ["quiz: 3/3", "could_break: <one sentence>", "residual_risk: <what you accept>"]
    out += ["## Sign", "", "Copy, keep one value per line, and submit as a PR review (**Request changes** or **Approve**, matching `decision`).", "",
            "```text", *tmpl, "```", ""]
    return out
