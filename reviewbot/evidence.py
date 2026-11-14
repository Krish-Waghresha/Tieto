"""Turn executed test results (TRX files from `dotnet test`) into graded proofs.

A proof without an execution record is never PASS: it is UNSUPPORTED ("not executed here").
"""
from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"t": "http://microsoft.com/schemas/VisualStudio/TeamTest/2010"}


def parse_trx(path: Path) -> list[dict]:
    root = ET.parse(path).getroot()
    out = []
    for r in root.iterfind(".//t:UnitTestResult", NS):
        msg = r.find(".//t:Output/t:ErrorInfo/t:Message", NS)
        out.append({
            "name": r.get("testName", ""),
            "outcome": r.get("outcome", ""),
            "duration": r.get("duration", ""),
            "message": (msg.text or "").strip()[:1500] if msg is not None else "",
        })
    return out


def load_runs(evidence_dir: Path) -> dict[str, dict]:
    """evidence_dir/<run>/results.trx plus evidence_dir/<run>/meta.json written by ci/run_proofs.sh."""
    runs = {}
    if not evidence_dir.exists():
        return runs
    for d in sorted(p for p in evidence_dir.iterdir() if p.is_dir()):
        meta_p = d / "meta.json"
        meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
        tests = []
        for trx in d.glob("*.trx"):
            tests += parse_trx(trx)
        runs[d.name] = {"meta": meta, "tests": tests}
    return runs


def evaluate(spec: list[dict], runs: dict[str, dict]) -> list[dict]:
    """spec item: id, title, run, filter (regex on test name), expect (all_pass|any_fail|observe), grade, claims."""
    proofs = []
    for p in spec:
        run = runs.get(p["run"])
        item = {k: v for k, v in p.items()}
        if run is None:
            item.update(status="not_executed", result="UNSUPPORTED", tests=[],
                        note="No execution record in this environment (proof is defined, not run).")
            proofs.append(item)
            continue
        meta = run["meta"]
        pat = re.compile(p["filter"])
        tests = [t for t in run["tests"] if pat.search(t["name"])]
        if p.get("exclude"):
            ex = re.compile(p["exclude"])
            tests = [t for t in tests if not ex.search(t["name"])]
        passed = sum(t["outcome"] == "Passed" for t in tests)
        failed = sum(t["outcome"] == "Failed" for t in tests)
        unknown = len(tests) - passed - failed
        if unknown:
            result = "UNSUPPORTED"
            note = f"{unknown} test(s) with outcome other than Passed/Failed (timeout, not executed, error) — never counted as a pass"
        elif not tests:
            result = "UNSUPPORTED"
            note = "No matching tests in the execution record (build failure or filter mismatch) — not a pass."
        elif p["expect"] == "all_pass":
            result = "HOLDS" if failed == 0 and passed > 0 else "VIOLATED"
            note = f"{passed} passed, {failed} failed"
        elif p["expect"] == "any_fail":
            result = "HOLDS" if failed > 0 else "VIOLATED"
            note = f"{failed} failed, {passed} passed (expected at least one failure)"
        else:  # observe
            result = "OBSERVED"
            note = f"{passed} passed, {failed} failed"
        item.update(
            status="executed",
            result=result,
            note=note,
            passed=passed,
            failed=failed,
            unknown=unknown,
            tests=tests[:12] if p["expect"] != "all_pass" or failed else [],
            test_count=len(tests),
            command=meta.get("command", ""),
            upstream_rev=meta.get("rev", ""),
            sdk=meta.get("sdk", ""),
            exit_code=meta.get("exit_code"),
            log_url=meta.get("log_url", ""),
        )
        proofs.append(item)
    return proofs


def outcome_of(proofs: list[dict], proof_id: str) -> dict | None:
    return next((p for p in proofs if p["id"] == proof_id), None)
