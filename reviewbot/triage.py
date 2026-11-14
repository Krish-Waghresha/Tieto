"""Deterministic verdict engine: policy rules → tier with reasons. No LLM input can change the tier.

Inspired by Rewind (2026): LLM findings are inputs, the verdict is plain, unit-tested code.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import csharp_graph
from .diffparse import FileDiff

TIERS = ["LIGHT", "STANDARD", "DEEP"]


def glob_to_re(pattern: str) -> re.Pattern:
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out += "(?:.*/)?"
            i += 3
        elif pattern.startswith("**", i):
            out += ".*"
            i += 2
        elif pattern[i] == "*":
            out += "[^/]*"
            i += 1
        else:
            out += re.escape(pattern[i])
            i += 1
    return re.compile(f"^{out}$")


def path_matches(path: str, patterns: list[str]) -> bool:
    return any(glob_to_re(p).match(path) for p in patterns)


@dataclass
class Fired:
    rule: str
    tier: str | None
    where: list[str]
    detail: str
    why: str
    motivated_by: str
    grade: str = "HEURISTIC"

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass
class Triage:
    tier: str
    fired: list[Fired] = field(default_factory=list)
    required_checks: list[dict] = field(default_factory=list)
    facts: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "fired": [f.to_dict() for f in self.fired],
            "required_checks": self.required_checks,
            "facts": self.facts,
        }


def _max_tier(a: str, b: str | None) -> str:
    if b is None:
        return a
    return a if TIERS.index(a) >= TIERS.index(b) else b


def run(files: list[FileDiff], policy: dict, sources: dict[str, tuple[str, str]], strip_prefix: str = "") -> Triage:
    """files: parsed diff; sources: path -> (base_text, head_text) for changed code files."""
    rules = {r["id"]: r for r in policy["rules"]}
    fired: list[Fired] = []
    facts: list[dict] = []
    required: list[dict] = []
    rel = lambda p: p[len(strip_prefix):] if strip_prefix and p.startswith(strip_prefix) else p

    def fire(rule_id: str, where: list[str], detail: str, grade: str = "HEURISTIC"):
        r = rules[rule_id]
        fired.append(Fired(rule_id, r.get("tier"), where, detail, r["why"], r["motivated_by"], grade))

    # R-POLICY-FILES (on full repo paths, not stripped)
    r = rules.get("R-POLICY-FILES")
    if r:
        hit = [f.path for f in files if path_matches(f.path, r["paths"])]
        if hit:
            fire("R-POLICY-FILES", hit, f"PR changes {len(hit)} policy/CI/build file(s)", "PROVEN")

    # protected paths
    prot = policy.get("protected_paths", {})
    hit = [f.path for f in files if path_matches(rel(f.path), prot.get("paths", []))]
    if hit:
        fired.append(Fired("PROTECTED-PATH", "DEEP", hit, "touches an always-human path", prot.get("why", ""), "policy.protected_paths", "PROVEN"))

    # R-DIAG-POLICY
    r = rules.get("R-DIAG-POLICY")
    if r:
        pats = [re.compile(p) for p in r["patterns"]]
        where = []
        for f in files:
            if not path_matches(rel(f.path), r["paths"]):
                continue
            for h in f.hunks:
                if any(p.search(l) for l in h.added + h.removed for p in pats):
                    where.append(h.short_id)
        if where:
            fire("R-DIAG-POLICY", where, f"{len(where)} changed block(s) alter diagnostic reporting in analyzer/generator code", "PROVEN")

    # R-CROSSCUT: field assignments changed → invocation fan-out
    r = rules.get("R-CROSSCUT")
    if r:
        for f in files:
            if f.path not in sources or not f.path.endswith(".cs"):
                continue
            base_txt, head_txt = sources[f.path]
            head_model = csharp_graph.parse(head_txt)
            for h in f.hunks:
                for fld, rhs in csharp_graph.assigned_fields(h.added):
                    if fld not in head_model.field_names():
                        continue
                    inv = csharp_graph.field_invocations(head_model, fld)
                    owners = sorted({o for _, o in inv})
                    facts.append({
                        "id": f"FACT-FANOUT-{fld}",
                        "kind": "fanout",
                        "grade": "HEURISTIC",
                        "grade_note": "text-level parse; Roslyn SymbolFinder would make this a PROVEN lower bound",
                        "text": f"`{fld}` is re-assigned at {h.short_id}; it is invoked at {len(inv)} call sites in {len(owners)} method(s): {', '.join(owners)}",
                        "field": fld,
                        "count": len(inv),
                        "methods": owners,
                        "lines": [l for l, _ in inv],
                        "claims": [h.id],
                        "new_rhs": rhs,
                    })
                    if len(inv) >= r["threshold"]:
                        fire("R-CROSSCUT", [h.short_id], f"`{fld}` re-assigned; reaches {len(inv)} call sites (threshold {r['threshold']})")

    # R-PUBLIC-API
    r = rules.get("R-PUBLIC-API")
    if r:
        pats = [re.compile(p) for p in r["added_patterns"]]
        where = [h.short_id for f in files if path_matches(rel(f.path), r["paths"]) and f.path.endswith(".cs")
                 for h in f.hunks if any(p.search(l) for l in h.added for p in pats)]
        if where:
            fire("R-PUBLIC-API", where, "new or changed public declarations")

    # R-SIZE
    r = rules.get("R-SIZE")
    if r:
        changed = sum(f.added + f.removed for f in files)
        if len(files) > r["max_files"] or changed > r["max_changed_lines"]:
            fire("R-SIZE", [f"{len(files)} files", f"{changed} lines"], "PR exceeds size limits", "PROVEN")
        facts.append({"id": "FACT-SIZE", "kind": "size", "grade": "PROVEN", "text": f"{len(files)} files, +{sum(f.added for f in files)} / -{sum(f.removed for f in files)} lines", "claims": []})

    # R-DOCS-POLICY
    r = rules.get("R-DOCS-POLICY")
    if r:
        where = [h.short_id for f in files if path_matches(rel(f.path), r["paths"]) for h in f.hunks]
        if where:
            fire("R-DOCS-POLICY", where, "documentation states behavior; must match an accepted decision", "PROVEN")

    # R-TESTS-ADDED → required check, not a tier
    r = rules.get("R-TESTS-ADDED")
    if r:
        test_files = [f for f in files if path_matches(rel(f.path), r["paths"])]
        if test_files:
            required.append({"rule": "R-TESTS-ADDED", "check": r["check"], "files": [f.path for f in test_files],
                             "why": r["why"], "motivated_by": r["motivated_by"]})

    # R-CHANGED-EXPECTATIONS: removed lines in existing test files
    r = rules.get("R-CHANGED-EXPECTATIONS")
    if r:
        where = [h.short_id for f in files if f.status == "M" and path_matches(rel(f.path), r["paths"])
                 for h in f.hunks if h.removed]
        if where:
            fire("R-CHANGED-EXPECTATIONS", where, "existing test lines modified or removed")

    # tier
    tier = policy.get("default_tier", "STANDARD")
    textual = bool(files) and all(f.hunks and not f.binary for f in files)
    all_ws = textual and all(h.whitespace_only() for f in files for h in f.hunks)
    docs_only = textual and all(rel(f.path).endswith(".md") for f in files)
    if (all_ws or docs_only) and not [x for x in fired if x.tier in ("STANDARD", "DEEP") and not (docs_only and x.rule == "R-DOCS-POLICY")]:
        tier = "LIGHT"
    for x in fired:
        if x.tier and not (tier == "LIGHT" and x.rule == "R-DOCS-POLICY"):
            tier = _max_tier(tier, x.tier)
    return Triage(tier=tier, fired=fired, required_checks=required, facts=facts)
