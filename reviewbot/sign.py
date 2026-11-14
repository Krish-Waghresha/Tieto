"""Validate a `/sign` PR review against the ledger and produce the decision record.

Rules enforced in code (not in prose):
- bound to the exact 40-char head SHA, the PR number, and the ledger hash the reviewer saw
- duplicate keys are rejected (no "D1: reject ... D1: accept" smuggling)
- every primary item has an explicit resolution; dependent items (follow_*) inherit unless overridden
- signer has write-level association, is not the PR author, not a head-commit author, not an agent account
- the GitHub review state must match the decision
- an approval cannot contain rejected / change-requested decisions or deferred abstentions
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


def parse(body: str) -> tuple[dict[str, str], list[str]]:
    out, dups = {}, []
    lines = body.strip().splitlines()
    if not lines or lines[0].strip() != "/sign":
        return {}, []
    for line in lines[1:]:
        if ":" in line:
            k, v = line.split(":", 1)
            k = k.strip()
            if k in out:
                dups.append(k)
            out[k] = v.strip()
    return out, dups


def validate(body: str, ledger: dict, signer: str, current_head: str, pr_author: str, review_state: str = "",
             author_association: str = "", head_commit_authors: list[str] | None = None, pr_number: int | None = None) -> dict:
    fields, dups = parse(body)
    errors, warnings = [], []
    if not fields:
        return {"ok": False, "errors": ["review body does not start with /sign"], "warnings": []}
    policy = ledger.get("signoff_policy", {})
    if dups:
        errors.append(f"duplicate keys are not allowed: {', '.join(sorted(set(dups)))}")

    # identity and separation of duties
    denied = {a.lower() for a in policy.get("agent_accounts_denied", [])}
    if signer.lower() in denied or signer.endswith("[bot]"):
        errors.append("bots and AI agent accounts cannot sign")
    allowed_assoc = policy.get("required_author_association")
    if allowed_assoc and author_association and author_association.upper() not in allowed_assoc:
        errors.append(f"signer association '{author_association}' is not one of {allowed_assoc}")
    if signer == pr_author:
        if policy.get("demo_allow_author_signoff"):
            warnings.append("SEPARATION OF DUTIES WAIVED FOR DEMO: signer is the PR author")
        else:
            errors.append("the PR author (the agent's operator) cannot sign; a different named engineer must")
    if policy.get("exclude_head_commit_authors") and head_commit_authors and signer in head_commit_authors and signer != pr_author:
        errors.append("a person who pushed commits to this PR cannot sign it")

    # binding to exactly what was reviewed
    if fields.get("head", "") != current_head or len(current_head) != 40:
        errors.append("the record must name the full 40-character PR head SHA it was made for — regenerate it from the latest report")
    if ledger["pin"].get("head") != current_head:
        errors.append("the evidence record was built for a different head — wait for the review bot to finish on the latest push")
    if pr_number is not None and str(ledger["pin"].get("pr")) != str(pr_number):
        errors.append("the evidence record belongs to a different PR")
    if fields.get("ledger", "") != ledger["ledger_sha256"][:12]:
        errors.append("the record was made from a different evidence record — reload the latest report")

    decision = fields.get("decision", "")
    if decision not in DECISIONS:
        errors.append(f"decision must be one of {sorted(DECISIONS)}")
    expected_state = {"approve": "approved", "request_changes": "changes_requested", "reject": "changes_requested"}.get(decision)
    if review_state and expected_state and review_state.lower() != expected_state:
        errors.append(f"GitHub review state is '{review_state.lower()}' but the record says '{decision}' — submit the review as "
                      f"{'Approve' if expected_state == 'approved' else 'Request changes'}")

    # resolutions
    kinds = {d["id"]: "D" for d in ledger["decisions"]} | {f["id"]: "F" for f in ledger["findings"]} | {a["id"]: "A" for a in ledger["abstentions"]}
    dependent = {d["id"]: d.get("recommended", "")[len("follow_"):] for d in ledger["decisions"] if str(d.get("recommended", "")).startswith("follow_")}
    resolutions = {}
    for iid, kind in kinds.items():
        v = fields.get(iid, "")
        if not v and iid in dependent:
            continue  # inherits from its parent below
        if v not in ALLOWED[kind]:
            errors.append(f"{iid}: '{v or 'missing'}' is not a valid resolution ({'/'.join(sorted(ALLOWED[kind]))})")
        resolutions[iid] = v
    for iid, parent in dependent.items():
        if iid not in resolutions:
            resolutions[iid] = resolutions.get(parent, "")
            warnings.append(f"{iid} follows {parent}: {resolutions[iid] or 'unresolved'}")
    if decision == "approve":
        blocking = [i for i, v in resolutions.items() if v in ("request_change", "reject", "defer")]
        if blocking:
            errors.append(f"cannot approve while {', '.join(blocking)} are request_change/reject/defer")
        valid_findings = [i for i, v in resolutions.items() if kinds[i] == "F" and v == "valid"]
        if valid_findings:
            warnings.append(f"approving with valid findings {valid_findings}: recorded as accepted residual risk")

    record = {
        "schema": "decision-first-review/decision-record@0.2",
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
        "signer_association": author_association,
        "github_review_state": review_state.lower(),
        "signed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "ai_counted_as_reviewer": False,
        "signature": "PROPOSED: Sigstore/in-toto attestation; demo relies on the GitHub identity of the reviewer",
    }
    record["record_sha256"] = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
    return {"ok": not errors, "errors": errors, "warnings": warnings, "record": record}
