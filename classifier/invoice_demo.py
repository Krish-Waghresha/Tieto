"""Run the trusted invoice fixture; keep authored AI claims separate from executable evidence."""
import argparse
import copy
import difflib
import hashlib
import json
import subprocess
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import engine

FIXTURE = engine.ROOT / "fixtures/invoice-import"
OUTPUT = engine.ROOT / "out/invoice-import"


def sources(folder):
    return {path.name: path.read_text() for path in sorted(folder.glob("*.cs"))}


def write_json(name, value):
    (OUTPUT / name).write_text(json.dumps(value, indent=2) + "\n")


def prepare():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    base = sources(FIXTURE / "base")
    changes = sources(FIXTURE / "head")
    tests = sources(FIXTURE / "tests")
    head = {**base, **changes}
    with tempfile.TemporaryDirectory(prefix="earned-invoice-") as temporary:
        before, after = Path(temporary) / "base", Path(temporary) / "head"
        before.mkdir()
        after.mkdir()
        for folder, snapshot in ((before, base), (after, head)):
            for name, text in snapshot.items():
                (folder / name).write_text(text)
        analysis = engine.extract(before, after)
    if any(analysis["errors"].values()):
        raise RuntimeError("Source-only PA failed: " + json.dumps(analysis["errors"]))
    requirements = json.loads((FIXTURE / "requirements.json").read_text())
    binding = {"base": analysis["baseHash"], "head": analysis["headHash"], "requirements": engine.digest(requirements)}
    executable, environment = engine.dotnet_command()
    build = subprocess.run([executable, "build", str(FIXTURE / "InvoiceImport.csproj"), "-c", "Release", "--nologo", "--verbosity", "quiet"],
        env=environment, capture_output=True, text=True, timeout=120)
    if build.returncode:
        raise RuntimeError(build.stdout + build.stderr)
    assembly = FIXTURE / "bin/Release/net8.0/InvoiceImport.dll"
    execution = subprocess.run([executable, str(assembly)], env=environment, capture_output=True, text=True, timeout=60)
    if execution.returncode not in (0, 1):
        raise RuntimeError(execution.stderr)
    results = json.loads(execution.stdout)
    identifiers = [test["id"] for test in results["tests"]]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Duplicate test identifiers")
    failures = {test["id"] for test in results["tests"] if test["status"] == "failed"}
    if failures != {"retry.lost-acknowledgement"}:
        raise ValueError("Unexpected fixture result; expected only the deliberate retry counterexample: " + str(failures))
    evidence = {
        "binding": binding,
        "execution": {"kind": "executed-local-dotnet", "trustedFixture": True, "modelExecuted": False,
            "timestamp": datetime.now(timezone.utc).isoformat(), "passed": results["passed"], "failed": results["failed"],
            "testSourceHash": engine.digest(tests), "assemblySha256": hashlib.sha256(assembly.read_bytes()).hexdigest(),
            "coverageMeaning": "Test-to-module associations are declared by the fixture, not measured line/branch coverage."},
        "tests": {test["id"]: test for test in results["tests"]},
    }
    old_tree = {"src/" + name: text for name, text in base.items()}
    new_tree = {**{"src/" + name: text for name, text in head.items()}, **{"tests/" + name: text for name, text in tests.items()}}
    patch = []
    stats = []
    for name in sorted(old_tree.keys() | new_tree.keys()):
        old_lines = old_tree.get(name, "").splitlines(keepends=True)
        new_lines = new_tree.get(name, "").splitlines(keepends=True)
        if old_lines == new_lines:
            continue
        added = deleted = 0
        for tag, old_start, old_end, new_start, new_end in difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False).get_opcodes():
            if tag in ("insert", "replace"):
                added += new_end - new_start
            if tag in ("delete", "replace"):
                deleted += old_end - old_start
        stats.append({"file": name, "added": added, "deleted": deleted})
        patch.extend(difflib.unified_diff(old_lines, new_lines, fromfile="a/" + name if name in old_tree else "/dev/null", tofile="b/" + name))
    summary = {"files": len(stats), "added": sum(item["added"] for item in stats), "deleted": sum(item["deleted"] for item in stats),
        "productionLines": sum(len(text.splitlines()) for text in changes.values()), "testLines": sum(len(text.splitlines()) for text in tests.values()),
        "perFile": stats, "analysisScope": "Production C# source. Test source is executed and included in the patch but not AI-reviewed."}
    if not 1000 <= summary["added"] + summary["deleted"] <= 2000:
        raise ValueError("The reference PR must contain 1,000-2,000 substantive changed source/test lines")
    (OUTPUT / "change.patch").write_text("".join(patch))
    write_json("pa.json", analysis)
    write_json("evidence.json", evidence)
    write_json("diff-stat.json", summary)
    return analysis, requirements, evidence, summary


def report(analysis, requirements, evidence, stats):
    authored = json.loads((FIXTURE / "judgments.json").read_text())
    if authored.get("testSourceHash") != evidence["execution"]["testSourceHash"]:
        raise ValueError("Test source changed since the authored judgments; review the fixture binding")
    judgments = copy.deepcopy(authored)
    for claim in judgments["claims"]:
        prefixes = claim.pop("testPrefixes")
        claim["tests"] = [test for test in evidence["tests"] if any(test.startswith(prefix) for prefix in prefixes)]
    classified = engine.classify_evidence(analysis, requirements, judgments, evidence)
    classified["diff"] = stats
    write_json("judgments.json", judgments)
    write_json("analysis.json", classified)
    priority = {"context": -1, "green": 0, "amber": 1, "gray": 2, "red": 3}
    modules = []
    for file in sorted(analysis["changedFiles"]):
        nodes = [node for node in classified["nodes"] if node.get("file") == file and node["change"] not in ("unchanged", "context")]
        strongest = max(nodes, key=lambda node: priority[node["color"]])
        modules.append({"file": file, "color": strongest["color"], "reason": strongest["reason"], "rule": strongest["rule"],
            "methods": sum(node["kind"] == "method" for node in nodes), "confidence": strongest["model"]["confidence"] if strongest["model"] else None})
    summary = {"mode": classified["mode"], "diff": {key: value for key, value in stats.items() if key != "perFile"},
        "checks": {"passed": evidence["execution"]["passed"], "failed": evidence["execution"]["failed"]},
        "moduleColors": dict(Counter(module["color"] for module in modules)), "modules": modules,
        "methodColors": dict(Counter(node["color"] for node in classified["nodes"] if node["kind"] == "method" and node["change"] not in ("unchanged", "context")))}
    write_json("summary.json", summary)
    lines = ["# Bulk Invoice Import: Evidence Review", "", f"Requirement: {requirements['id']}. {stats['added']} additions, {stats['deleted']} deletions, {stats['files']} changed source/test files.", "",
        "Real Roslyn PA and locally executed checks. AI judgments and confidence values are authored demonstration inputs, not a live model or calibrated reliability.", "",
        f"Checks: {evidence['execution']['passed']} passed; {evidence['execution']['failed']} failed. The retry failure is intentional: expected one persisted invoice, observed two.", "",
        "| Module | Attention | Why |", "| --- | --- | --- |"]
    lines.extend(f"| {module['file']} | {module['color']} | {module['reason']} |" for module in modules)
    lines.extend(["", "## Limits", "", "- New behavioral implementations can be green; whitespace is not the green criterion.",
        "- Test associations are module-level, not measured line/branch coverage or exhaustive proofs.",
        "- Public declarations are included in the authored module judgments; Roslyn compiles them but does not prove their contracts.",
        "- Supporting local tests do not clear callers of risky dependencies.", "- Test source is not AI-reviewed in this output.",
        "- No merge approval, live provider verification, held-out benchmark, or review-time claim.",
        "- Existing PR and playground are not replaced by this command.", ""])
    (OUTPUT / "review.md").write_text("\n".join(lines))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true", help="Generate PA, tests and source bindings before authoring judgments")
    args = parser.parse_args()
    analysis, requirements, evidence, stats = prepare()
    if args.prepare:
        print(json.dumps({"binding": evidence["binding"], "testSourceHash": evidence["execution"]["testSourceHash"], "added": stats["added"], "files": stats["files"],
            "checks": {"passed": evidence["execution"]["passed"], "failed": evidence["execution"]["failed"]}}, indent=2))
    else:
        summary = report(analysis, requirements, evidence, stats)
        print(json.dumps({key: value for key, value in summary.items() if key != "modules"}, indent=2))


if __name__ == "__main__":
    main()