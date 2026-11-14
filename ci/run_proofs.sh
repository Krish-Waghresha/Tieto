#!/usr/bin/env bash
# Runs the executable proofs for the demo PR against the upstream repository (untrusted code: CI sandbox only).
# Usage: ci/run_proofs.sh <upstream-dir> <evidence-dir> [pr-head-sha]
# Runs from the BASE checkout: pinned upstream SHAs come from the base's sample/UPSTREAM.json; PR files are read as data.
set -uo pipefail
UP="$1"; EV="$2"; PR_HEAD="${3:-HEAD}"; HERE="$(cd "$(dirname "$0")" && pwd)"; ROOT="$(cd "$HERE/.." && pwd)"
BASE=$(python3 -I -c "import json;print(json.load(open('$ROOT/sample/UPSTREAM.json'))['base_sha'])")
HEAD=$(python3 -I -c "import json;print(json.load(open('$ROOT/sample/UPSTREAM.json'))['head_sha'])")
PROJ=tests/MessagePack.SourceGenerator.Tests
GEN_TESTS=$PROJ/GenericsFormatterTests.cs
ANA_TESTS=$PROJ/MsgPack00xAnalyzerTests.cs
mkdir -p "$EV"
SDK=$(dotnet --version 2>/dev/null || echo "missing")
RUN_URL="${GITHUB_SERVER_URL:-}/${GITHUB_REPOSITORY:-}/actions/runs/${GITHUB_RUN_ID:-}"

inject_p4() {  # insert the probe test before the final closing brace of the test class
  python3 -I - "$UP/$ANA_TESTS" "$HERE/P4_test.cs.txt" <<'PY'
import sys
p, t = sys.argv[1], open(sys.argv[2]).read()
s = open(p, encoding="utf-8-sig").read()
i = s.rstrip().rfind("}")
open(p, "w", encoding="utf-8").write(s[:i] + t + "\n" + s[i:])
PY
}

meta() {  # run-name rev command exit
  python3 -I - "$EV/$1/meta.json" "$2" "$3" "$4" "$SDK" "$RUN_URL" <<'PY'
import json, sys, os
os.makedirs(os.path.dirname(sys.argv[1]), exist_ok=True)
json.dump({"rev": sys.argv[2], "command": sys.argv[3], "exit_code": int(sys.argv[4]), "sdk": sys.argv[5], "log_url": sys.argv[6]}, open(sys.argv[1], "w"))
PY
}

# P0 provenance: the files under review in the PR are byte-identical to the upstream agent commit
python3 -I - "$ROOT" "$UP" "$HEAD" "$EV/provenance.json" "$PR_HEAD" <<'PY'
import hashlib, json, subprocess, sys, pathlib
root, up, head, out, pr_head = sys.argv[1:]
files = []
names = subprocess.run(["git", "-C", root, "ls-tree", "-r", "--name-only", pr_head, "--", "sample/"], capture_output=True, text=True).stdout.split()
for name in sorted(names):
    rel = name[len("sample/"):]
    if rel in ("UPSTREAM.json", "LICENSE"):
        continue
    pr_bytes = subprocess.run(["git", "-C", root, "show", f"{pr_head}:{name}"], capture_output=True).stdout
    upstream = subprocess.run(["git", "-C", up, "show", f"{head}:{rel}"], capture_output=True).stdout
    files.append({"path": rel, "pr_sha256": hashlib.sha256(pr_bytes).hexdigest(),
                  "upstream_sha256": hashlib.sha256(upstream).hexdigest()})
for f in files:
    f["match"] = f["pr_sha256"] == f["upstream_sha256"]
meta = json.load(open(pathlib.Path(root, "sample/UPSTREAM.json")))
json.dump(dict(meta, files=files, all_match=all(f["match"] for f in files)), open(out, "w"), indent=2)
print("provenance all_match:", all(f["match"] for f in files))
PY

# Run A: base code + the agent's new tests + probe P4  (P2, P4b)
git -C "$UP" checkout -q -f "$BASE"
git -C "$UP" show "$HEAD:$GEN_TESTS" > "$UP/$GEN_TESTS"
inject_p4
CMD="dotnet test $PROJ -f net8.0 --filter \"FullyQualifiedName~FromMetadataReference|FullyQualifiedName~NullStringKey_PositionalRecord\""
( cd "$UP" && dotnet test $PROJ -f net8.0 --filter "FullyQualifiedName~FromMetadataReference|FullyQualifiedName~NullStringKey_PositionalRecord" \
    --logger "trx;LogFileName=results.trx" --results-directory "$EV/base-with-head-tests" ) > "$EV/base-with-head-tests.log" 2>&1
meta base-with-head-tests "$BASE" "$CMD (on base, with head's GenericsFormatterTests.cs)" $?

# Run B: head code + probe P4, whole generator test project  (P1, P3, P4h)
git -C "$UP" checkout -q -f "$HEAD"
inject_p4
CMD="dotnet test $PROJ -f net8.0"
( cd "$UP" && dotnet test $PROJ -f net8.0 --logger "trx;LogFileName=results.trx" --results-directory "$EV/head" ) > "$EV/head.log" 2>&1
meta head "$HEAD" "$CMD" $?

tail -n 5 "$EV/base-with-head-tests.log" "$EV/head.log"
exit 0
