"""Create the controlled synthetic branches and PR without changing any existing branch."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from urllib.parse import quote
from xml.etree import ElementTree

from github_review import api, mermaid, playground_link, REPOSITORY, BASE_BRANCH, HEAD_BRANCH

ROOT = Path(__file__).resolve().parent


def prepare(api_call=api):
    repository = api_call(f"repos/{REPOSITORY}")
    if not repository.get("private"):
        raise ValueError("The synthetic demo repository must remain private")
    existing = api_call(f"repos/{REPOSITORY}/git/matching-refs/heads/synthetic/")
    refs = {item["ref"]: item["object"]["sha"] for item in existing}
    required = {"refs/heads/" + BASE_BRANCH, "refs/heads/" + HEAD_BRANCH}
    if required & refs.keys() and not required <= refs.keys():
        raise ValueError("Partial synthetic branch setup exists; refusing to overwrite it")
    if not required <= refs.keys():
        fixture = ROOT / "fixtures/order-flow"
        extras = {
            "requirement.md": (fixture / "requirement.md").read_text(),
            "README.md": "# HarborOrders synthetic review example\n\nDeveloper-authored C# source snapshots for an attention-classification prototype.\nNo production code or incident claims. Colors are computed from the PR diff.\n",
        }
        commits = {}
        for side in ("base", "head"):
            contents = {path.name: path.read_text() for path in sorted((fixture / side).glob("*.cs"))} | extras
            tree = api_call(f"repos/{REPOSITORY}/git/trees", method="POST", body={"tree": [
                {"path": path, "mode": "100644", "type": "blob", "content": text} for path, text in contents.items()
            ]})
            commit = api_call(f"repos/{REPOSITORY}/git/commits", method="POST", body={
                "message": "Synthetic baseline: order submission" if side == "base" else "Synthetic PR: bulk pricing and contrasting review cases",
                "tree": tree["sha"], "parents": [] if side == "base" else [commits["base"]],
            })
            commits[side] = commit["sha"]
        for side, branch in (("base", BASE_BRANCH), ("head", HEAD_BRANCH)):
            api_call(f"repos/{REPOSITORY}/git/refs", method="POST", body={"ref": "refs/heads/" + branch, "sha": commits[side]})
    pulls = api_call(f"repos/{REPOSITORY}/pulls?state=open&base=synthetic%2Fbase&per_page=100", paginate=True)
    existing_pr = next((item for item in pulls if item["head"]["ref"] == HEAD_BRANCH), None)
    if existing_pr:
        return {"state": "already-open", "number": existing_pr["number"], "url": existing_pr["html_url"]}
    pull = api_call(f"repos/{REPOSITORY}/pulls", method="POST", body={
        "base": BASE_BRANCH, "head": HEAD_BRANCH, "title": "ORD-17: bulk pricing (synthetic classifier demo)",
        "body": "Add a 10% subtotal discount for orders of five or more units. Authorization and receipt behavior must remain unchanged.\n\nThis is a deliberately mixed synthetic change used to demonstrate attention classification, not a production fix. The reviewer reads the actual base/head source; no expected colors are supplied to it.",
    })
    return {"state": "created", "number": pull["number"], "url": pull["html_url"]}


INVOICE_BASE = "synthetic/invoice-base"
INVOICE_HEAD = "synthetic/invoice-import"
INVOICE_MARKER = "<!-- earned-invoice-evidence-v2 -->"
INVOICE_LEGACY_README = "# Bulk invoice import reference\n\nSynthetic C# review example for INV-BULK-26. The baseline supports single-invoice import; the feature adds bulk ingestion, validation, retries, preview, and reconciliation.\n\nOn the feature branch, run `dotnet run --project InvoiceImport.csproj` with .NET 8. One test deliberately fails: losing a commit acknowledgement creates two invoices instead of one. It is a review counterexample, not a production implementation to deploy.\n\nPA and tests are real. The evidence comment uses authored, uncalibrated AI judgments; it does not claim a live AI call, a merge approval, or exhaustive coverage. The invoice playground is not connected yet.\n"


def invoice_contents():
    import invoice_demo

    fixture = invoice_demo.FIXTURE
    project = ElementTree.fromstring((fixture / "InvoiceImport.csproj").read_text())
    project.find("PropertyGroup/OutputType").set("Condition", "Exists('tests/Checks.cs')")
    group = project.find("ItemGroup")
    for item in list(group):
        if item.get("Include") == "base/*.cs":
            item.set("Include", "src/*.cs")
        elif item.get("Include") == "head/*.cs":
            group.remove(item)
    ElementTree.indent(project, space="  ")
    common = {
        "InvoiceImport.csproj": ElementTree.tostring(project, encoding="unicode") + "\n",
        "requirements.json": (fixture / "requirements.json").read_text(),
        "README.md": "# Bulk invoice import\n\nINV-BULK-26 adds CSV ingestion, normalization, validation, retries, preview, and reconciliation.\n\nUse **Open interactive review** in the PR's change-map comment to inspect the evidence, answer policy questions, and explore the retry behavior.\n\n## Run the checks\n\nWith .NET 8: `dotnet run --project InvoiceImport.csproj`. The lost-acknowledgement check identifies duplicate persistence: two invoices instead of one.\n\n## Provenance\n\nThis reference combines executed source analysis and checks with authored AI judgments. Confidence values and interactive outcome mappings are illustrative.\n",
    }
    base = {"src/" + name: text for name, text in invoice_demo.sources(fixture / "base").items()} | common
    head = base | {"src/" + name: text for name, text in invoice_demo.sources(fixture / "head").items()} | {
        "tests/" + name: text for name, text in invoice_demo.sources(fixture / "tests").items()}
    return base, head


def blob_sha(text):
    raw = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def verify_invoice_tree(contents, tree):
    if tree.get("truncated"):
        raise ValueError("Invoice source tree is truncated")
    actual = {item["path"]: item["sha"] for item in tree["tree"] if item["type"] == "blob" and item["mode"] == "100644"}
    expected = {path: blob_sha(text) for path, text in contents.items()}
    if actual != expected or any(item["type"] not in ("blob", "tree") or item["mode"] not in ("100644", "040000") for item in tree["tree"]):
        raise ValueError("Invoice branch differs from the reviewed fixture; refusing to overwrite it")


def invoice_comment(pr, analysis, summary, playground=None):
    modules = summary["modules"]
    by_id = {node["id"]: node for node in analysis["nodes"]}
    files = {module["file"] for module in modules}
    edges = set()
    for edge in analysis["edges"]:
        source = by_id.get(edge["source"], {}).get("file")
        target = by_id.get(edge["target"], {}).get("file")
        if source in files and target in files and source != target:
            edges.add((source, target))
    graph = {"nodes": [{"id": item["file"], "label": Path(item["file"]).stem, "color": item["color"]} for item in modules],
        "edges": [{"source": source, "target": target, "change": "unchanged"} for source, target in sorted(edges)]}
    counts = summary["methodColors"]
    revision = pr["head"]["sha"]
    source_root = f"https://github.com/{REPOSITORY}/blob/{revision}/"
    lines = [INVOICE_MARKER, f'<!-- analysis:{analysis["reviewKey"]} head:{revision} -->', "### Evidence-based change map", "",
        f'**{summary["diff"]["added"]:,} added lines / {summary["diff"]["files"]} files** · {counts.get("green", 0)} green / {counts.get("amber", 0)} amber / {counts.get("red", 0)} red / {counts.get("gray", 0)} gray changed methods.', "",
        *([f'**[Open interactive review]({playground})**', ""] if playground else []),
        "```mermaid", mermaid(graph), "```", "",
        f'**Checks:** {summary["checks"]["passed"]} passed; {summary["checks"]["failed"]} retry-integrity failure. Expected **1 invoice**, observed **2**.', "",
        "<details><summary>Reasons, confidence, and source evidence</summary>", "",
        "| Module | Attention | Compliance confidence | Why |", "| --- | --- | --- | --- |"]
    for module in modules:
        confidence = "Not assessed" if module["color"] == "gray" else f'{module["confidence"]:.0%}'
        source = source_root + "src/" + quote(module["file"], safe="")
        reason = module["reason"].replace("|", "\\|").replace("\n", " ")
        lines.append(f'| [{Path(module["file"]).stem}]({source}) | {module["color"]} | {confidence} | {reason} |')
    lines += ["", f'[Requirements: INV-BULK-26]({source_root}requirements.json) · [Executable checks]({source_root}tests) · [Retry counterexample]({source_root}tests/WorkflowChecks.cs)', "",
        "</details>", "", "<details><summary>Provenance</summary>", "",
        "Source analysis and checks were executed locally. AI judgments, confidence values, and interactive outcome mappings are authored demo inputs; confidence is not calibrated. Tests support module-level claims, not exhaustive coverage. The interactive link uses the local review server.", "", "</details>"]
    return "\n".join(lines)


def prepare_invoice(api_call=api):
    import invoice_demo

    repository = api_call(f"repos/{REPOSITORY}")
    if not repository.get("private"):
        raise ValueError("The invoice demo repository must remain private")
    analysis, requirements, evidence, stats = invoice_demo.prepare()
    summary = invoice_demo.report(analysis, requirements, evidence, stats)
    classified = json.loads((invoice_demo.OUTPUT / "analysis.json").read_text())
    contents = dict(zip(("base", "head"), invoice_contents()))
    refs = {item["ref"]: item["object"]["sha"] for item in api_call(f"repos/{REPOSITORY}/git/matching-refs/heads/synthetic/invoice")}
    if "refs/heads/" + INVOICE_HEAD in refs and "refs/heads/" + INVOICE_BASE not in refs:
        raise ValueError("Invoice head exists without its baseline; refusing to overwrite it")
    commits = {}
    for side, branch in (("base", INVOICE_BASE), ("head", INVOICE_HEAD)):
        ref = "refs/heads/" + branch
        if ref in refs:
            commit = api_call(f"repos/{REPOSITORY}/git/commits/{refs[ref]}")
            remote_tree = api_call(f"repos/{REPOSITORY}/git/trees/{commit['tree']['sha']}?recursive=1")
            try:
                verify_invoice_tree(contents[side], remote_tree)
            except ValueError:
                verify_invoice_tree({**contents[side], "README.md": INVOICE_LEGACY_README}, remote_tree)
                tree = api_call(f"repos/{REPOSITORY}/git/trees", method="POST", body={"base_tree": commit["tree"]["sha"], "tree": [
                    {"path": "README.md", "mode": "100644", "type": "blob", "content": contents[side]["README.md"]}]})
                parents = [commit["sha"]] + ([commits["base"]] if side == "head" else [])
                commit = api_call(f"repos/{REPOSITORY}/git/commits", method="POST", body={"message": "Connect invoice interactive review guide", "tree": tree["sha"], "parents": parents})
                api_call(f"repos/{REPOSITORY}/git/refs/heads/{branch}", method="PATCH", body={"sha": commit["sha"], "force": False})
        else:
            tree = api_call(f"repos/{REPOSITORY}/git/trees", method="POST", body={"tree": [
                {"path": path, "mode": "100644", "type": "blob", "content": text} for path, text in sorted(contents[side].items())]})
            commit = api_call(f"repos/{REPOSITORY}/git/commits", method="POST", body={
                "message": "Invoice baseline: single-invoice ingestion" if side == "base" else "INV-BULK-26: bulk invoice import with evidence review cases",
                "tree": tree["sha"], "parents": [] if side == "base" else [commits["base"]]})
        verify_invoice_tree(contents[side], api_call(f"repos/{REPOSITORY}/git/trees/{commit['tree']['sha']}?recursive=1"))
        if side == "head" and commits["base"] not in [parent["sha"] for parent in commit["parents"]]:
            raise ValueError("Invoice head does not descend directly from the reviewed baseline")
        commits[side] = commit["sha"]
        if ref not in refs:
            api_call(f"repos/{REPOSITORY}/git/refs", method="POST", body={"ref": ref, "sha": commit["sha"]})
    pulls = api_call(f"repos/{REPOSITORY}/pulls?state=open&base={quote(INVOICE_BASE, safe='')}&per_page=100", paginate=True)
    existing = next((item for item in pulls if item["head"]["ref"] == INVOICE_HEAD), None)
    pr = existing or api_call(f"repos/{REPOSITORY}/pulls", method="POST", body={
        "base": INVOICE_BASE, "head": INVOICE_HEAD,
        "title": "INV-BULK-26: bulk invoice import",
        "body": "Add bulk CSV invoice ingestion, normalization, validation, retries, preview, and reconciliation. Requirement: INV-BULK-26. See the change-map comment for the interactive review.",
    })
    endpoint = f"repos/{REPOSITORY}/pulls/{pr['number']}"
    current = api_call(endpoint)
    if current["base"]["sha"] != commits["base"] or current["head"]["sha"] != commits["head"]:
        raise ValueError("Invoice PR changed before evidence publication")
    remote_files = api_call(endpoint + "/files?per_page=100", paginate=True)
    observed = {item["filename"]: (item["additions"], item["deletions"]) for item in remote_files}
    expected = {item["file"]: (item["added"], item["deleted"]) for item in stats["perFile"]}
    if observed != expected:
        raise ValueError("GitHub diff does not match the measured fixture; no evidence comment published")
    if current["title"] != "INV-BULK-26: bulk invoice import":
        api_call(endpoint, method="PATCH", body={"title": "INV-BULK-26: bulk invoice import"})
    playground = playground_link(current, classified["reviewKey"])[0]
    enriched = {**classified, "github": {"repository": REPOSITORY, "number": current["number"], "base": commits["base"], "head": commits["head"], "url": current["html_url"]}}
    invoice_demo.write_json("playground.json", enriched)
    destination = ROOT / "out/playground" / f"pr-{current['number']}" / classified["reviewKey"] / "index.html"
    subprocess.run(["node", str(ROOT / "web/build.mjs"), str(invoice_demo.OUTPUT / "playground.json"), str(destination)], cwd=ROOT, check=True, capture_output=True, text=True, timeout=120)
    login = api_call("user")["login"]
    comments_endpoint = f"repos/{REPOSITORY}/issues/{pr['number']}/comments"
    comments = api_call(comments_endpoint + "?per_page=100", paginate=True)
    own = next((item for item in comments if item["user"]["login"] == login and item.get("body", "").startswith(INVOICE_MARKER)), None)
    body = invoice_comment(current, classified, summary, playground)
    latest = api_call(endpoint)
    if latest["base"]["sha"] != commits["base"] or latest["head"]["sha"] != commits["head"]:
        raise ValueError("Invoice PR changed while preparing the comment")
    comment = own if own and own["body"] == body else api_call(
        f"repos/{REPOSITORY}/issues/comments/{own['id']}" if own else comments_endpoint,
        method="PATCH" if own else "POST", body={"body": body})
    api_call(endpoint, method="PATCH", body={"title": "INV-BULK-26: bulk invoice import",
        "body": "Add bulk CSV invoice ingestion, normalization, validation, retries, preview, and reconciliation.\n\nRequirement: **INV-BULK-26** in requirements.json.\n\n" + f"**[Open interactive review]({playground})**\n\n" +
        f"{stats['added']:,} added lines across {stats['files']} files. Review the change map, inspect source evidence, clarify duplicate policy, and explore the retry-integrity failure.\n\n<details><summary>Provenance</summary>\n\nSource analysis and tests are executed. AI judgments, confidence values, and interactive outcome mappings are authored for this reference. The review link uses the local server.\n\n</details>"})
    result = {"state": "already-open" if existing else "created", "number": pr["number"], "url": pr["html_url"],
        "comment": comment["html_url"], "head": commits["head"], "base": commits["base"],
        "added": stats["added"], "deleted": stats["deleted"], "files": stats["files"], "playground": playground}
    invoice_demo.write_json("github.json", result)
    (invoice_demo.OUTPUT / "github-comment.md").write_text(body + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invoice", action="store_true")
    arguments = parser.parse_args()
    print(json.dumps(prepare_invoice() if arguments.invoice else prepare(), indent=2))