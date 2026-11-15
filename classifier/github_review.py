"""Publish one compact, revision-bound graph on a private synthetic GitHub PR."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import tempfile
import threading
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit

import engine

REPOSITORY = "Krish-Waghresha/earned-review-demo"
BASE_BRANCH = "synthetic/base"
HEAD_BRANCH = "synthetic/order-pricing"
MARKER = "<!-- earned-classifier-v1 -->"
LABELS = {"green": "Light review", "amber": "Inspect behavior", "red": "Human attention", "gray": "Insufficient evidence", "context": "Unchanged"}
COLORS = {
    "green": "fill:#237a46,stroke:#185832,color:#ffffff",
    "amber": "fill:#9c6500,stroke:#704900,color:#ffffff",
    "red": "fill:#b42332,stroke:#851b26,color:#ffffff",
    "gray": "fill:#5b6472,stroke:#3e4652,color:#ffffff",
    "context": "fill:#ffffff,stroke:#b3b9b0,color:#626962,stroke-dasharray:4 3",
}


def api(endpoint: str, *, method: str = "GET", body=None, paginate: bool = False):
    arguments = ["gh", "api", endpoint, "--method", method]
    if body is not None:
        arguments += ["--input", "-"]
    if paginate:
        arguments += ["--paginate", "--slurp"]
    for attempt in range(3 if method == "GET" else 1):
        result = subprocess.run(arguments, input=json.dumps(body) if body is not None else None,
            text=True, capture_output=True, timeout=60)
        transient = any(message in result.stderr.lower() for message in ("timeout", "connection reset", "unexpected eof"))
        if result.returncode == 0 or not transient or attempt == 2:
            break
    if result.returncode:
        raise RuntimeError(f"GitHub {method} failed for {endpoint}: {result.stderr.strip()}")
    output = json.loads(result.stdout) if result.stdout.strip() else None
    return [item for page in output for item in page] if paginate else output


def validate_pr(pr: dict):
    if pr.get("state") != "open":
        raise ValueError("PR is not open")
    if pr["base"]["repo"]["full_name"] != REPOSITORY or pr["head"]["repo"]["full_name"] != REPOSITORY:
        raise ValueError("Only the configured same-repository demo PR is supported")
    if pr["base"]["ref"] != BASE_BRANCH or pr["head"]["ref"] != HEAD_BRANCH:
        raise ValueError("PR is not the configured synthetic example")
    for side in ("base", "head"):
        if not re.fullmatch(r"[0-9a-f]{40}", pr[side]["sha"]):
            raise ValueError("Invalid revision")
    if not 1 <= pr.get("changed_files", 0) <= 30:
        raise ValueError("PR exceeds the prototype changed-file scope")


def label(value: str, limit: int = 52) -> str:
    clean = re.sub(r"[^A-Za-z0-9_.():, ?+-]", "", str(value))
    return clean[:limit] or "Block"


def mermaid(analysis: dict) -> str:
    identifiers = {node["id"]: f"n{index}" for index, node in enumerate(analysis["nodes"])}
    lines = ["flowchart LR"]
    for node in analysis["nodes"]:
        color = node["color"] if node["color"] in COLORS else "gray"
        lines.append(f'  {identifiers[node["id"]]}["{label(node["label"])}<br/>{LABELS[color]}"]:::{color}')
    for edge in analysis["edges"]:
        if edge["source"] in identifiers and edge["target"] in identifiers:
            arrow = "-.->" if edge.get("change") in ("added", "removed") else "-->"
            lines.append(f'  {identifiers[edge["source"]]} {arrow} {identifiers[edge["target"]]}')
    lines += [f"  classDef {name} {style}" for name, style in COLORS.items()]
    return "\n".join(lines)


def source_link(pr: dict, node: dict) -> str:
    source = node.get("after") or node.get("before") or {}
    revision = pr["head"]["sha"] if node.get("after") else pr["base"]["sha"]
    path = quote(node.get("file", ""), safe="/")
    return f'https://github.com/{REPOSITORY}/blob/{revision}/{path}#L{source.get("line", 1)}'


def playground_link(pr: dict, key: str) -> tuple[str, bool]:
    base = os.environ.get("EARNED_PLAYGROUND_URL", "http://127.0.0.1:5174").rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or any(char.isspace() for char in base):
        raise ValueError("EARNED_PLAYGROUND_URL must be an HTTP(S) base URL without credentials, query, or fragment")
    path = f"pr-{int(pr['number'])}/{quote(key, safe='')}/index.html"
    return quote(base, safe=":/%") + "/" + path, parsed.hostname in ("127.0.0.1", "localhost", "::1")


def render_comment(pr: dict, analysis: dict, key: str) -> str:
    changed = [node for node in analysis["nodes"] if node["change"] not in ("unchanged", "context")]
    mode = "PA + model" if analysis["mode"] == "hybrid" else "PA-only; model not run"
    reasons = [f'- [{label(node["label"])}]({source_link(pr, node)}): {label(node["reason"], 160)}.' for node in changed]
    playground, local = playground_link(pr, key)
    return "\n".join([
        MARKER, f"<!-- analysis:{key} -->", "### Change map", "", "```mermaid", mermaid(analysis), "```", "",
        f'**[Open interactive playground]({playground})**' + (" · local demo; start the playground server on this machine." if local else ""), "",
        "Green: light review · Amber: inspect · Red: human attention · Gray: unknown. Outlined: unchanged context.", "",
        f'Roslyn {analysis["tool"]["version"]} · {mode} · `{pr["head"]["sha"][:8]}`. Attention, not merge approval.', "",
        "<details><summary>Why these colors</summary>", "", *reasons, "",
        "Green is a scoped whitespace check. Synthetic example; classifier reliability is not calibrated.",
        "</details>",
    ])


def added_lines(patch: str) -> set[int]:
    result = set()
    line = None
    for text in str(patch or "").splitlines():
        match = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@", text)
        if match:
            line = int(match[1])
        elif line is not None and text.startswith("+"):
            result.add(line)
            line += 1
        elif line is not None and text.startswith(" "):
            line += 1
    return result


def annotations(analysis: dict, files: list[dict]) -> tuple[list[dict], list[str]]:
    patches = {item["filename"]: added_lines(item.get("patch", "")) for item in files}
    comments, skipped = [], []
    for node in analysis["nodes"]:
        if node["color"] not in ("red", "gray") or node["change"] not in ("added", "modified") or node["kind"] != "method":
            continue
        source = node.get("after") or {}
        matching = sorted(line for line in patches.get(node["file"], set()) if source.get("line", 0) <= line <= source.get("endLine", -1))
        if not matching:
            skipped.append(node["label"])
            continue
        comments.append({"path": node["file"], "line": matching[0], "side": "RIGHT",
            "body": f'**{LABELS[node["color"]]}: {label(node["label"])}**\n\n{node["reason"]}.\n\nBasis: Roslyn facts + `{node["rule"]}` policy rule. Not a merge verdict.'})
    return comments, skipped


def unpublished_annotations(comments: list[dict], existing: list[dict], head: str, login: str) -> list[dict]:
    return [comment for comment in comments if not any(
        item.get("user", {}).get("login") == login and item.get("commit_id") == head and
        item.get("path") == comment["path"] and item.get("line", item.get("original_line")) == comment["line"] and
        item.get("body") == comment["body"] for item in existing)]


def read_snapshot(sha: str, destination: Path, api_call=api, cache: dict | None = None) -> dict[str, str]:
    cache = cache if cache is not None else {}
    tree = api_call(f"repos/{REPOSITORY}/git/trees/{sha}?recursive=1")
    if tree.get("truncated"):
        raise ValueError("Truncated repository tree")
    entries = [item for item in tree["tree"] if item["type"] != "tree"]
    if len(entries) > 50:
        raise ValueError("Repository exceeds the 50-file prototype limit")
    files = {}
    total = 0
    for item in entries:
        path = PurePosixPath(item["path"])
        if path.is_absolute() or ".." in path.parts or "\\" in str(path) or item["mode"] not in ("100644", "100755") or item["type"] != "blob":
            raise ValueError("Unsupported repository entry")
        if item.get("size", 0) > 500000:
            raise ValueError("Source file exceeds prototype size limit")
        if item["sha"] not in cache:
            cache[item["sha"]] = api_call(f"repos/{REPOSITORY}/git/blobs/{item['sha']}")
        blob = cache[item["sha"]]
        if blob.get("encoding") != "base64":
            raise ValueError("Unsupported Git blob encoding")
        raw = base64.b64decode(blob["content"])
        total += len(raw)
        if total > 2000000 or b"\x00" in raw:
            raise ValueError("Binary or oversized input is not supported")
        text = raw.decode("utf-8")
        target = destination.joinpath(*path.parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        files[str(path)] = text
    return files


def fingerprint(pr: dict, use_model: bool) -> str:
    files = ["policy.json", "engine.py", "github_review.py", "analyzer/Program.cs", "analyzer/Analyzer.csproj"]
    return engine.digest({"base": pr["base"]["sha"], "head": pr["head"]["sha"], "model": use_model,
        "playground": os.environ.get("EARNED_PLAYGROUND_URL", "http://127.0.0.1:5174"),
        "modelConfigured": bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")),
        "engine": {name: (engine.ROOT / name).read_text() for name in files}})


def ensure_current(expected: dict, actual: dict):
    validate_pr(actual)
    if any(expected[side]["sha"] != actual[side]["sha"] for side in ("base", "head")):
        raise ValueError("PR changed during analysis; no result published for the new revision")


def review(number: int, *, publish: bool = False, use_model: bool = False, api_call=api, analyze=engine.run) -> dict:
    endpoint = f"repos/{REPOSITORY}/pulls/{number}"
    pr = api_call(endpoint)
    validate_pr(pr)
    key = fingerprint(pr, use_model)
    login = api_call("user")["login"]
    existing = next((item for item in api_call(f"repos/{REPOSITORY}/issues/{number}/comments?per_page=100", paginate=True)
        if item["user"]["login"] == login and item.get("body", "").startswith(MARKER)), None)
    if publish and existing and f"<!-- analysis:{key} -->" in existing["body"]:
        return {"state": "already-current", "url": existing["html_url"]}
    if publish and existing:
        api_call(f"repos/{REPOSITORY}/issues/comments/{existing['id']}", method="PATCH", body={"body": MARKER + f'\nUpdating analysis for `{pr["head"]["sha"][:8]}`. Previous colors are not clearance for this revision.'})
    files = api_call(endpoint + "/files?per_page=100", paginate=True)
    with tempfile.TemporaryDirectory(prefix="earned-pr-") as directory:
        base, head = Path(directory) / "base", Path(directory) / "head"
        cache = {}
        base_files = read_snapshot(pr["base"]["sha"], base, api_call, cache)
        read_snapshot(pr["head"]["sha"], head, api_call, cache)
        requirement = base_files.get("requirement.md", "Requirement not supplied; do not infer acceptance criteria.")
        analysis = analyze(base, head, requirement, use_model=use_model)
    if set(analysis["changedFiles"]) != {item["filename"] for item in files} or len(files) != pr["changed_files"]:
        raise ValueError("Analyzed file set does not match the complete PR diff")
    analysis["github"] = {"repository": REPOSITORY, "number": number, "base": pr["base"]["sha"], "head": pr["head"]["sha"], "url": pr["html_url"]}
    body = render_comment(pr, analysis, key)
    comments, skipped = annotations(analysis, files)
    destination = engine.ROOT / "out" / f"pr-{number}"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "analysis.json").write_text(json.dumps(analysis, indent=2) + "\n")
    (destination / "comment.md").write_text(body + "\n")
    playground = engine.ROOT / "out/playground" / f"pr-{number}" / key / "index.html"
    subprocess.run(["node", str(engine.ROOT / "web/build.mjs"), str(destination / "analysis.json"), str(playground)],
        cwd=engine.ROOT, check=True, capture_output=True, text=True, timeout=60)
    review_body = f'<!-- earned-graph-inline:{key} -->\nAttention points for `{pr["head"]["sha"][:8]}`. See the change-map comment.'
    payload = {"commit_id": pr["head"]["sha"], "event": "COMMENT", "body": review_body, "comments": comments}
    (destination / "review.json").write_text(json.dumps(payload, indent=2) + "\n")
    if not publish:
        return {"state": "preview", "output": str(destination), "inlineComments": len(comments), "unanchored": skipped}
    ensure_current(pr, api_call(endpoint))
    previous_comments = api_call(endpoint + "/comments?per_page=100", paginate=True)
    new_comments = unpublished_annotations(comments, previous_comments, pr["head"]["sha"], login)
    if new_comments:
        api_call(endpoint + "/reviews", method="POST", body={**payload, "comments": new_comments})
    ensure_current(pr, api_call(endpoint))
    posted = api_call(f"repos/{REPOSITORY}/issues/comments/{existing['id']}" if existing else f"repos/{REPOSITORY}/issues/{number}/comments",
        method="PATCH" if existing else "POST", body={"body": body})
    return {"state": "published", "url": posted["html_url"], "inlineComments": len(comments), "newInlineComments": len(new_comments), "unanchored": skipped, "mode": analysis["mode"], "playground": playground_link(pr, key)[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int)
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--model", choices=("off", "gemini"), default="off")
    args = parser.parse_args()
    if args.watch:
        if not args.publish:
            parser.error("--watch requires --publish")
        stop = threading.Event()
        print(f"Watching {REPOSITORY}: {BASE_BRANCH} <- {HEAD_BRANCH}; poll interval 15s", flush=True)
        try:
            while not stop.is_set():
                try:
                    pulls = api(f"repos/{REPOSITORY}/pulls?state=open&base={quote(BASE_BRANCH, safe='')}&per_page=100", paginate=True)
                    for pr in pulls:
                        if pr["head"]["ref"] == HEAD_BRANCH:
                            result = review(pr["number"], publish=True, use_model=args.model == "gemini")
                            if result["state"] != "already-current":
                                print(json.dumps(result), flush=True)
                except (RuntimeError, ValueError, subprocess.SubprocessError, OSError) as error:
                    print(f"Analysis unavailable; no green clearance: {type(error).__name__}: {error}", flush=True)
                stop.wait(15)
        except KeyboardInterrupt:
            stop.set()
    else:
        if not args.pr or args.pr < 1:
            parser.error("Provide --pr NUMBER or --watch --publish")
        print(json.dumps(review(args.pr, publish=args.publish, use_model=args.model == "gemini"), indent=2))


if __name__ == "__main__":
    main()