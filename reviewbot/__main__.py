"""CLI.

  python -m reviewbot review --base B --head H --out out/ [--evidence evidence/] [--pr N --repo o/r --author login]
  python -m reviewbot sign --ledger out/ledger.json --body-file comment.txt --signer login --head SHA --author login
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ledger as ledger_mod
from . import render_html, render_md, sign


def cmd_review(a) -> int:
    policy = json.loads(Path(a.policy).read_text())
    review_input = json.loads(Path(a.input).read_text())
    prov = json.loads(Path(a.provenance).read_text()) if a.provenance and Path(a.provenance).exists() else None
    if prov is None and Path("sample/UPSTREAM.json").exists():
        prov = json.loads(Path("sample/UPSTREAM.json").read_text())
    L = ledger_mod.build(repo=".", base=a.base, head=a.head, prefix=a.prefix, policy=policy, review_input=review_input,
                         evidence_dir=Path(a.evidence), provenance=prov,
                         pr={"repo": a.repo, "number": a.pr, "author": a.author})
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "ledger.json").write_text(json.dumps(L, indent=2, default=str))
    (out / "comment.md").write_text(render_md.render(L, report_url=a.report_url, prefix=a.prefix))
    (out / "report.html").write_text(render_html.render(L, prefix=a.prefix))
    print(json.dumps({"tier": L["triage"]["tier"], "open_items": L["open_items"], "coverage_complete": L["coverage"]["complete"],
                      "problems": L["problems"], "ledger": L["ledger_sha256"][:12]}))
    return 0


def cmd_sign(a) -> int:
    L = json.loads(Path(a.ledger).read_text())
    res = sign.validate(Path(a.body_file).read_text(), L, a.signer, a.head, a.author, review_state=a.review_state)
    Path(a.out).write_text(json.dumps(res, indent=2))
    print(json.dumps({"ok": res["ok"], "errors": res["errors"], "warnings": res["warnings"]}))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="reviewbot")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review")
    r.add_argument("--base", required=True)
    r.add_argument("--head", required=True)
    r.add_argument("--prefix", default="sample/")
    r.add_argument("--policy", default="review-policy.json")
    r.add_argument("--input", default="demo/MP-2283/review-input.json")
    r.add_argument("--evidence", default="evidence")
    r.add_argument("--provenance", default="evidence/provenance.json")
    r.add_argument("--out", default="out")
    r.add_argument("--repo", default="")
    r.add_argument("--pr", default=None)
    r.add_argument("--author", default="")
    r.add_argument("--report-url", default="")
    r.set_defaults(fn=cmd_review)
    s = sub.add_parser("sign")
    s.add_argument("--ledger", required=True)
    s.add_argument("--body-file", required=True)
    s.add_argument("--signer", required=True)
    s.add_argument("--head", required=True)
    s.add_argument("--author", required=True)
    s.add_argument("--review-state", default="")
    s.add_argument("--out", default="out/sign-result.json")
    s.set_defaults(fn=cmd_sign)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
