"""Assemble the review ledger: the single source every view (PR comment, HTML, audio) is rendered from."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import csharp_graph, diffparse, evidence, triage

GRADE_OF_KIND = {"ABSTAINED": "ABSTAINED", "UNSUPPORTED": "UNSUPPORTED"}


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def run_fact_checks(checks: list[dict], texts: dict[str, dict[str, str]], requirement: str) -> list[dict]:
    out = []
    for c in checks:
        src = requirement if c["rev"] == "requirement" else texts.get(c["rev"], {}).get(c.get("path", ""), "")
        pat = re.compile(c["pattern"])
        hits = [i for i, line in enumerate(src.splitlines(), 1) if pat.search(line)]
        absent_ok = True
        if c.get("absent_pattern"):
            absent_ok = not any(re.search(c["absent_pattern"], l) for l in src.splitlines())
        if not src:
            holds = None
        else:
            holds = (not hits) if c.get("expect_absent") else (bool(hits) and absent_ok)
        out.append({
            "id": c["id"], "kind": "grep", "grade": "PROVEN" if src else "UNSUPPORTED",
            "grade_note": "exact text match on the pinned revision (text-level, not semantic)",
            "text": c["text"], "holds": holds, "count": len(hits), "lines": hits[:20],
            "rev": c["rev"], "path": c.get("path", c["rev"]), "claims": [],
        })
    return out


def branch_facts(head_model: csharp_graph.Model, fanout: list[dict]) -> list[dict]:
    out = []
    for f in fanout:
        for name in re.findall(r"\b([A-Z]\w+)\s*\(", f.get("new_rhs", "")):
            for m in head_model.by_name(name):
                shapes = csharp_graph.branch_shape(m)
                if not shapes:
                    continue
                s = shapes[0]
                out.append({
                    "id": f"FACT-BRANCH-{name}", "kind": "branch", "grade": "HEURISTIC",
                    "grade_note": "text-level branch shape; Roslyn ControlFlowGraph proposed",
                    "text": f"`{name}` (lines {m.start}-{m.end}) calls {', '.join(s['then_calls']) or 'nothing'} only when `{s['cond']}`; "
                            + ("otherwise it takes an else branch." if s["has_else"] else "otherwise it does nothing (no else branch)."),
                    "method": name, "cond": s["cond"], "then_calls": s["then_calls"], "has_else": s["has_else"],
                    "lines": [m.start, m.end], "claims": [],
                })
    return out


def fill(template: str, facts: dict[str, dict]) -> tuple[str, list[str]]:
    used = []

    def rep(m):
        fid, attr = m.group(1), m.group(2)
        used.append(fid)
        v = facts.get(fid, {}).get(attr)
        return str(v) if v is not None else f"⟨missing {fid}.{attr}⟩"

    return re.sub(r"\{(FACT-[\w-]+)\.(\w+)\}", rep, template), used


def phantom_numbers(text: str, allowed: set[str]) -> list[str]:
    """Numbers in free text that do not come from a fact/proof value or an ID (anti-phantom check)."""
    clean = re.sub(r"#L\d+|\b[A-Z]{1,4}\d+\b|MsgPack\d+|AD\d+|#\d+|\bAC\d\b|\[\d\]", "", text)
    return [n for n in re.findall(r"\b\d+\b", clean) if n not in allowed]


def check_rule(rule: dict, proof: dict | None) -> bool:
    if not proof or proof.get("status") != "executed":
        return False
    tests = proof.get("tests", [])
    msgs = " ".join(t.get("message", "") for t in tests)
    if "failed_min" in rule and proof.get("failed", 0) < rule["failed_min"]:
        return False
    if "passed_min" in rule and proof.get("passed", 0) < rule["passed_min"]:
        return False
    if "message_any" in rule and not any(s in msgs for s in rule["message_any"]):
        return False
    return True


def build(*, repo: str, base: str, head: str, prefix: str, policy: dict, review_input: dict,
          evidence_dir: Path, provenance: dict | None, pr: dict) -> dict:
    files = diffparse.parse(diffparse.git_diff(base, head, None, cwd=repo))  # WHOLE repo: policy/CI files are visible
    for f in files:  # sample files: paths relative to the upstream project root; everything else keeps its repo path
        f.in_sample = bool(prefix) and f.path.startswith(prefix)
        f.repo_path = f.path
        if f.in_sample:
            f.path = f.path[len(prefix):]
            for h in f.hunks:
                h.path = f.path
    texts = {"base": {}, "head": {}}
    sources = {}
    for f in files:
        b = diffparse.show(base, f.repo_path, cwd=repo)
        h = diffparse.show(head, f.repo_path, cwd=repo)
        texts["base"][f.path], texts["head"][f.path] = b, h
        sources[f.path] = (b, h)
    for chk in review_input.get("fact_checks", []):  # make sure referenced files are loaded
        p = chk.get("path")
        if p and p not in texts.get(chk["rev"], {}) and chk["rev"] in ("base", "head"):
            texts[chk["rev"]][p] = diffparse.show(base if chk["rev"] == "base" else head, prefix + p, cwd=repo)

    requirement = (Path(repo) / review_input["requirement_file"]).read_text() if review_input.get("requirement_file") else ""

    # [1] triage (deterministic)
    tri = triage.run(files, policy, sources)

    # facts
    head_models = {p: csharp_graph.parse(h) for p, (_, h) in sources.items() if p.endswith(".cs")}
    facts = list(tri.facts)
    for p, m in head_models.items():
        facts += branch_facts(m, [f for f in tri.facts if f["kind"] == "fanout"])
    facts += run_fact_checks(review_input.get("fact_checks", []), texts, requirement)
    if provenance and provenance.get("files"):
        facts.append({
            "id": "FACT-PROVENANCE", "kind": "provenance", "grade": "PROVEN",
            "grade_note": "sha256 of each file in the PR vs the upstream agent commit, computed in CI",
            "text": f"Files under review are byte-identical to upstream {provenance.get('repo')} @ {str(provenance.get('head_sha'))[:7]} "
                    f"({sum(f['match'] for f in provenance['files'])}/{len(provenance['files'])} files match)",
            "holds": bool(provenance.get("all_match")), "count": len(provenance["files"]), "lines": [], "claims": [],
        })
    fact_by_id = {f["id"]: f for f in facts}

    # [2] proofs
    runs = evidence.load_runs(evidence_dir)
    proofs = evidence.evaluate(review_input.get("proofs", []), runs)
    if provenance and provenance.get("files"):
        p0 = {"id": "P0", "title": "Files under review are byte-identical to the upstream agent commit", "grade": "PROVEN",
              "status": "executed", "result": "HOLDS" if provenance.get("all_match") else "VIOLATED",
              "note": f"{sum(f['match'] for f in provenance['files'])}/{len(provenance['files'])} files match (sha256)", "claims": [], "tests": []}
    else:
        p0 = {"id": "P0", "title": "Files under review are byte-identical to the upstream agent commit", "grade": "PROVEN",
              "status": "not_executed", "result": "UNSUPPORTED", "note": "Provenance check runs in CI; not executed here.", "claims": [], "tests": []}
    proofs = [p0] + proofs
    proof_by_id = {p["id"]: p for p in proofs}

    hunks = [h for f in files for h in f.hunks]
    hunk_ids = {h.id for h in hunks}
    allowed_numbers = {str(v) for f in facts for k, v in f.items() if isinstance(v, int)}
    allowed_numbers |= {str(x) for f in facts for x in f.get("lines", [])}

    problems = []

    # [3] decisions — validate citations (drop decisions that cite nothing)
    decisions = []
    for d in review_input.get("decisions", []):
        bad = [c for c in d.get("claims", []) if c not in hunk_ids]
        missing_facts = [x for x in d.get("facts", []) if x not in fact_by_id]
        if not d.get("claims"):
            problems.append({"kind": "invented-decision", "id": d["id"], "text": "cites no hunk — dropped"})
            continue
        before, _ = fill(d["before"], fact_by_id)
        after, _ = fill(d["after"], fact_by_id)
        phantoms = phantom_numbers(before + " " + after, allowed_numbers)
        dd = dict(d, before=before, after=after, bad_claims=bad, missing_facts=missing_facts, phantom_numbers=phantoms,
                  grade="ARGUED", evidence=[proof_by_id[e] for e in d.get("evidence", []) if e in proof_by_id])
        if bad or missing_facts or phantoms:
            problems.append({"kind": "citation", "id": d["id"], "text": f"bad hunks {bad}, missing facts {missing_facts}, unbacked numbers {phantoms}"})
        decisions.append(dd)

    # findings — G-Research rule: the model suggests, the evidence decides
    findings = []
    for fnd in review_input.get("findings", []):
        confirm = all(check_rule(r, proof_by_id.get(pid)) for pid, r in fnd.get("confirm_if", {}).items())
        disprove = any(check_rule(r, proof_by_id.get(pid)) for pid, r in fnd.get("disprove_if", {}).items())
        fact_ok = all(fact_by_id.get(x, {}).get("holds") is True for x in fnd.get("facts", []))
        executed = all(proof_by_id.get(pid, {}).get("status") == "executed" for pid in fnd.get("confirm_if", {}))
        if disprove:
            status, grade = "DISPROVED", "MEASURED"
        elif confirm:
            status, grade = "CONFIRMED", "MEASURED"
        elif executed:
            status, grade = "NOT CONFIRMED", "MEASURED"
        else:
            status, grade = ("SUPPORTED BY FACTS, NOT EXECUTED" if fact_ok else "FACTS DO NOT HOLD"), "ARGUED"
        findings.append(dict(fnd, status=status, grade=grade,
                             evidence=[proof_by_id[e] for e in fnd.get("evidence", []) if e in proof_by_id]))

    abstentions = [dict(a, grade=GRADE_OF_KIND.get(a["kind"], "ABSTAINED")) for a in review_input.get("abstentions", [])]

    # [4] coverage — every hunk claimed by a decision, finding or fact
    claimed: dict[str, list[str]] = {h.id: [] for h in hunks}
    for d in decisions:
        for c in d["claims"]:
            claimed.setdefault(c, []).append(d["id"])
    for fnd in findings:
        for c in fnd.get("claims", []):
            claimed.setdefault(c, []).append(fnd["id"])
    for fct in facts:
        for c in fct.get("claims", []):
            if c in claimed:
                claimed[c].append(fct["id"])
    unexplained = [h.id for h in hunks if not claimed.get(h.id)]

    # code excerpts for the UI (from the pinned revisions only; rendered as text, never executed)
    def excerpt(text: str, start: int, length: int, ctx: int = 3, cap: int = 40) -> dict:
        lines = text.splitlines()
        lo = max(1, start - ctx)
        hi = min(len(lines), start + max(length, 1) - 1 + ctx, lo + cap - 1)
        return {"start": lo, "lines": lines[lo - 1:hi], "focus": [start, start + max(length, 1) - 1]}
    snippets = {}
    for f in files:
        b_txt, h_txt = texts["base"].get(f.path, ""), texts["head"].get(f.path, "")
        for h in f.hunks:
            before = excerpt(b_txt, h.old_start if h.old_len else h.old_start + 1, h.old_len) if b_txt else None
            if before is not None and h.old_len == 0:
                before["focus"] = [0, -1]  # pure insertion: nothing was here before
                before["insertion"] = True
            snippets[h.id] = {"path": f.path, "lang": "csharp" if f.path.endswith(".cs") else "markdown",
                              "before": before, "after": excerpt(h_txt, h.new_start, h.new_len) if h_txt else None}
    for fct in facts:
        if fct["kind"] == "branch" and fct.get("lines"):
            m_start, m_end = fct["lines"]
            path = next((p for p, m in head_models.items() if m.by_name(fct["method"])), None)
            if path:
                snippets[f"method:{fct['method']}"] = {"path": path, "lang": "csharp", "before": None,
                                                       "after": excerpt(texts["head"][path], m_start, m_end - m_start + 1, ctx=0)}
    coverage = {
        "hunks": [dict(h.to_dict(), claimed_by=claimed.get(h.id, [])) for h in hunks],
        "unexplained": unexplained,
        "complete": not unexplained,
    }

    # scope fan-out check: requirement-anchored sites vs reach of each decision
    scope = []
    base_sites = fact_by_id.get("FACT-BASE-SITES")
    for d in decisions:
        reach = max([fact_by_id[x]["count"] for x in d.get("facts", []) if x in fact_by_id and fact_by_id[x]["kind"] == "fanout"] or [0])
        if reach and base_sites:
            live_fixed = len([h for h in hunks if any("DeclaringSyntaxReferences[0]" in l for l in h.removed)])
            ratio = reach / max(live_fixed, 1)
            scope.append({"decision": d["id"], "requirement_sites": live_fixed, "reach": reach, "ratio": round(ratio, 1),
                          "mismatch": ratio >= 3, "grade": "HEURISTIC",
                          "text": f"The requirement asks to fix {live_fixed} crashing lookups. {d['id']} changes how all {reach} diagnostic call sites behave "
                                  f"({ratio:.0f}× wider than the fix needs)."})

    # tier: coverage gaps and scope mismatches raise it (never lower)
    tier = tri.tier
    if unexplained or any(s["mismatch"] for s in scope):
        tier = "DEEP"

    # quiz answer keys from facts/proofs, not from an LLM
    quiz = []
    for q in review_input.get("quiz", []):
        qq = dict(q)
        if q.get("options_from") == "fanout":
            n = fact_by_id.get(q["fact"], {}).get("count")
            if n:
                opts = sorted({n, 2, n + 6})
                qq["options"] = [str(o) for o in opts]
                qq["answer"] = opts.index(n)
                qq["key_grade"] = "HEURISTIC"
        elif q.get("kind") == "line":
            qq["options"] = [h.id for h in hunks if h.path.endswith(".cs") and "/tests/" not in "/" + h.path][:5]
            fan = next((f for f in facts if f["kind"] == "fanout"), None)
            key = fan["claims"][0] if fan and fan.get("claims") else q["answer"]
            qq["answer"] = qq["options"].index(key) if key in qq["options"] else 0
            qq["key_grade"] = fan["grade"] if fan else "ARGUED"
        elif q.get("answer_from_proof"):
            p = proof_by_id.get(q["answer_from_proof"])
            if p and p.get("status") == "executed":
                msgs = " ".join(t.get("message", "") for t in p.get("tests", []))
                if p.get("passed"):
                    qq["answer"] = 1
                else:
                    qq["answer"] = next((i for s, i in q["answer_rule"].items() if s in msgs), q["fallback_answer"])
                qq["key_grade"] = "MEASURED"
                qq["explain"] = "From the executed probe on the old code (P4b)."
            else:
                qq["answer"] = q["fallback_answer"]
                qq["key_grade"] = "ARGUED"
                qq["explain"] = "Expected from reading the code; the probe on the old code (P4b) has not run yet, so this key is AI reasoning."
        quiz.append(qq)

    for rc in tri.required_checks:
        if rc["rule"] == "R-TESTS-ADDED":
            p1, p2 = proof_by_id.get("P1"), proof_by_id.get("P2")
            if p1 and p2 and p1.get("status") == p2.get("status") == "executed":
                rc["status"] = "HOLDS" if p1["result"] == p2["result"] == "HOLDS" else "VIOLATED"
            else:
                rc["status"] = "NOT RUN"
            rc["proofs"] = ["P1", "P2"]

    # verdict
    open_items = [d["id"] for d in decisions if d.get("recommended") not in ("accept",) and not str(d.get("recommended", "")).startswith("follow_")] \
        + [f["id"] for f in findings if f["status"] != "DISPROVED"] + [a["id"] for a in abstentions]
    dependent_items = [d["id"] for d in decisions if str(d.get("recommended", "")).startswith("follow_")]
    counts = {}
    for item in [*facts, *proofs]:
        g = item.get("grade") if item.get("status") != "not_executed" else "UNSUPPORTED"
        counts[g] = counts.get(g, 0) + 1
    for d in decisions:
        counts["ARGUED"] = counts.get("ARGUED", 0) + 1
    for f in findings:
        counts[f["grade"]] = counts.get(f["grade"], 0) + 1
    for a in abstentions:
        counts[a["grade"]] = counts.get(a["grade"], 0) + 1

    ledger = {
        "schema": "decision-first-review/ledger@0.1",
        "status_note": "DEMO / reference implementation — not a product. Decision extraction is SIMULATED (hand-written stand-in for an LLM pass); facts, triage, coverage and proofs are computed.",
        "pin": {
            "repo": pr.get("repo", ""), "pr": pr.get("number"), "base": base, "head": head,
            "pr_author": pr.get("author", ""), "upstream": provenance or {},
            "policy_sha256": _sha(json.dumps(policy, sort_keys=True)),
            "requirement_id": review_input["requirement_id"],
            "requirement_sha256": _sha(requirement),
        },
        "requirement": {"id": review_input["requirement_id"], "file": review_input.get("requirement_file"),
                        "acceptance_criteria": review_input.get("acceptance_criteria", {}),
                        "trace": review_input.get("acceptance_criteria_trace", {})},
        "provenance_note": review_input.get("provenance", {}),
        "triage": dict(tri.to_dict(), tier=tier, base_tier=tri.tier),
        "facts": facts,
        "proofs": proofs,
        "decisions": decisions,
        "findings": findings,
        "abstentions": abstentions,
        "coverage": coverage,
        "snippets": snippets,
        "scope": scope,
        "not_checked": review_input.get("not_checked", []),
        "what_to_do": review_input.get("what_to_do", [])[:3],
        "quiz": quiz,
        "grade_counts": counts,
        "open_items": open_items,
        "dependent_items": dependent_items,
        "problems": problems,
        "files": [{"path": f.path, "repo_path": f.repo_path, "in_sample": f.in_sample, "binary": f.binary, "status": f.status,
                   "added": f.added, "removed": f.removed, "hunks": len(f.hunks)} for f in files],
        "summary": review_input.get("summary", ""),
        "owners": policy.get("owners", []),
        "signoff_policy": policy.get("signoff", {}),
    }
    ledger["ledger_sha256"] = _sha(json.dumps({k: v for k, v in ledger.items() if k != "ledger_sha256"}, sort_keys=True, default=str))
    return ledger
