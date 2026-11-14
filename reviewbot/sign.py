"""Validate a `/sign` PR review against the ledger and produce the decision record.

Rules enforced in code (not in prose):
- the record is bound to the current head SHA and the ledger hash it was made from
- every decision, finding and abstention has an explicit resolution
- the signer is not the PR author (the agent's operator) unless the demo policy waives it, loudly
- an approval cannot contain rejected or change-requested decisions, or deferred abstentions
- the AI never signs
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

ALLOWED = {
    "D": {"accept", "request_change", "reject"},
    "F": {"valid", "invalid"},
    "A": {"resolved", "accept_risk", "defer"},
}
DECISIONS = {"approve", "request_changes", "reject"}
BOT_LOGINS = {"github-actions[bot]", "github-actions"}


def parse(body: str) -> dict[str, str]:
    out = {}
    lines = body.strip().splitlines()
    if not lines or lines[0].strip() != "/sign":
        return {}
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def validate(body: str, ledger: dict, signer: str, current_head: str, pr_author: str, review_state: str = "") -> dict:
    fields = parse(body)
    errors, warnings = [], []
    if not fields:
        return {"ok": False, "errors": ["comment does not start with /sign"], "warnings": []}
    if signer in BOT_LOGINS or signer.endswith("[bot]"):
        errors.append("bots and AI agents cannot sign")
    head = fields.get("head", "")
    if not head or not current_head.startswith(head):
        errors.append(f"record is for head {head[:7] or '?'} but the PR head is {current_head[:7]} — evidence is stale, regenerate")
    if fields.get("ledger", "") != ledger["ledger_sha256"][:12]:
        errors.append("record was made from a different ledger — reload the latest report")
    decision = fields.get("decision", "")
    if decision not in DECISIONS:
        errors.append(f"decision must be one of {sorted(DECISIONS)}")
    expected_state = {"approve": "approved", "request_changes": "changes_requested", "reject": "changes_requested"}.get(decision)
    if review_state and expected_state and review_state.lower() != expected_state:
        errors.append(f"GitHub review state is '{review_state.lower()}' but the record says '{decision}' — submit the review as "
                      f"{'Approve' if expected_state == 'approved' else 'Request changes'}")
    policy = ledger.get("signoff_policy", {})
    if signer == pr_author:
        if policy.get("demo_allow_author_signoff"):
            warnings.append("SEPARATION OF DUTIES WAIVED FOR DEMO: signer is the PR author")
        else:
            errors.append("signer is the PR author (the agent's operator); a different named engineer must sign")
    items = {d["id"]: "D" for d in ledger["decisions"]} | {f["id"]: "F" for f in ledger["findings"]} | {a["id"]: "A" for a in ledger["abstentions"]}
    resolutions = {}
    for iid, kind in items.items():
        v = fields.get(iid, "")
        if v not in ALLOWED[kind]:
            errors.append(f"{iid}: '{v or 'missing'}' is not a valid resolution ({'/'.join(sorted(ALLOWED[kind]))})")
        resolutions[iid] = v
    if decision == "approve":
        blocking = [i for i, v in resolutions.items() if v in ("request_change", "reject", "defer")]
        if blocking:
            errors.append(f"cannot approve while {', '.join(blocking)} are request_change/reject/defer")
        valid_findings = [i for i, v in resolutions.items() if items[i] == "F" and v == "valid"]
        if valid_findings:
            warnings.append(f"approving with valid findings {valid_findings}: recorded as accepted residual risk")
    record = {
        "schema": "decision-first-review/decision-record@0.1",
        "requirement": ledger["requirement"]["id"],
        "repo": ledger["pin"]["repo"], "pr": ledger["pin"]["pr"],
        "base": ledger["pin"]["base"], "head": current_head,
        "ledger_sha256": ledger["ledger_sha256"], "policy_sha256": ledger["pin"]["policy_sha256"],
        "tier": ledger["triage"]["tier"], "tier_rules": [f["rule"] for f in ledger["triage"]["fired"]],
        "checked": [{"id": p["id"], "what": p["title"], "by": "tool (CI)", "grade": p["grade"], "result": p.get("result")}
                    for p in ledger["proofs"] if p.get("status") == "executed"]
                   + [{"id": f["id"], "what": f["text"], "by": "tool (bot)", "grade": f["grade"]} for f in ledger["facts"]],
        "not_checked": ledger["not_checked"] + [p["id"] + ": " + p["title"] for p in ledger["proofs"] if p.get("status") != "executed"],
        "resolutions": resolutions,
        "quiz": fields.get("quiz", "not taken"),
        "could_break": fields.get("could_break", ""),
        "residual_risk": fields.get("residual_risk", ""),
        "decision": decision,
        "signer": signer,
        "github_review_state": review_state.lower(),
        "signed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ai_counted_as_reviewer": False,
        "signature": "PROPOSED: Sigstore/in-toto attestation; demo relies on the GitHub identity of the comment author",
    }
    record["record_sha256"] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    return {"ok": not errors, "errors": errors, "warnings": warnings, "record": record}
