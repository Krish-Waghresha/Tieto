"""Unit tests for the deterministic parts: verdict engine, C# facts, anti-phantom, sign rules."""
import json
import unittest
from pathlib import Path

import os
import subprocess
import tempfile

from reviewbot import csharp_graph, diffparse, evidence, ledger, render_md, sign, triage

ROOT = Path(__file__).resolve().parents[1]
POLICY = json.loads((ROOT / "review-policy.json").read_text())


def fd(path, added=(), removed=(), status="M", start=10):
    h = diffparse.Hunk(path, start, len(removed), start, len(added), list(removed), list(added))
    return diffparse.FileDiff(path, status, [h])


class TriageTests(unittest.TestCase):
    def test_docs_only_is_light(self):
        t = triage.run([fd("docs/guide.md", ["new sentence"])], POLICY, {})
        self.assertEqual(t.tier, "LIGHT")

    def test_whitespace_only_code_is_light(self):
        t = triage.run([fd("src/Lib/Foo.cs", ["    int x = 1;"], ["  int x = 1;"])], POLICY, {})
        self.assertEqual(t.tier, "LIGHT")

    def test_plain_code_change_defaults_to_standard_never_light(self):
        t = triage.run([fd("src/Lib/Foo.cs", ["int x = 2;"], ["int x = 1;"])], POLICY, {})
        self.assertEqual(t.tier, "STANDARD")

    def test_policy_file_change_forces_deep(self):
        t = triage.run([fd("review-policy.json", ['"threshold": 1000'], ['"threshold": 10'])], POLICY, {})
        self.assertEqual(t.tier, "DEEP")
        self.assertIn("R-POLICY-FILES", [f.rule for f in t.fired])

    def test_ci_change_forces_deep(self):
        t = triage.run([fd(".github/workflows/x.yml", ["run: echo hi"])], POLICY, {})
        self.assertEqual(t.tier, "DEEP")

    def test_protected_path_forces_deep(self):
        t = triage.run([fd("src/auth/Token.cs", ["return true;"], ["return false;"])], POLICY, {})
        self.assertEqual(t.tier, "DEEP")

    def test_diagnostic_policy_change_in_analyzer_is_deep(self):
        t = triage.run([fd("src/X/CodeAnalysis/C.cs", ["reportDiagnostic?.Invoke(d);"], ["report(d);"])], POLICY, {})
        self.assertEqual(t.tier, "DEEP")

    def test_tests_added_is_a_required_check_not_a_tier(self):
        t = triage.run([fd("tests/X/FooTests.cs", ["[Fact] public void A() {}"], status="A")], POLICY, {})
        self.assertEqual(t.tier, "STANDARD")
        self.assertEqual(t.required_checks[0]["rule"], "R-TESTS-ADDED")

    def test_size_limit_forces_deep(self):
        files = [fd(f"src/F{i}.cs", ["x"]) for i in range(101)]
        self.assertEqual(triage.run(files, POLICY, {}).tier, "DEEP")


SRC = """namespace N;
public class C
{
    private readonly Action<int>? report;
    private C(Action<int>? r)
    {
        this.report = r is null ? null : d => Filter(r, d);
    }
    public void A() { this.report?.Invoke(1); this.report?.Invoke(2); }
    // this.report?.Invoke(3);
    public void B() { this.report(4); }
    private void Filter(Action<int> r, int d)
    {
        if (d > 0)
        {
            r(d);
        }
    }
}
"""


class CSharpFactTests(unittest.TestCase):
    def test_fanout_ignores_comments_and_counts_direct_calls(self):
        m = csharp_graph.parse(SRC)
        inv = csharp_graph.field_invocations(m, "report")
        self.assertEqual(len(inv), 3)
        self.assertEqual({o for _, o in inv}, {"A", "B"})

    def test_branch_shape_detects_missing_else(self):
        m = csharp_graph.parse(SRC)
        shape = csharp_graph.branch_shape(m.by_name("Filter")[0])[0]
        self.assertFalse(shape["has_else"])
        self.assertIn("r", shape["then_calls"])

    def test_assigned_fields(self):
        self.assertEqual(csharp_graph.assigned_fields(["this.report = x;"])[0][0], "report")


class AntiPhantomTests(unittest.TestCase):
    def test_numbers_must_come_from_facts(self):
        self.assertEqual(ledger.phantom_numbers("reaches 28 call sites", {"28"}), [])
        self.assertEqual(ledger.phantom_numbers("reaches 30 call sites", {"28"}), ["30"])

    def test_ids_are_not_numbers(self):
        self.assertEqual(ledger.phantom_numbers("see D1, F1, AC1, MsgPack005, #2305, Foo.cs#L239", set()), [])

    def test_template_fill(self):
        txt, used = ledger.fill("{FACT-X.count} sites", {"FACT-X": {"count": 28}})
        self.assertEqual(txt, "28 sites")


HEAD = "1234567" + "0" * 33
LEDGER = {
    "ledger_sha256": "abcdef1234567890",
    "requirement": {"id": "MP-1"},
    "pin": {"repo": "o/r", "pr": 1, "base": "b" * 40, "head": HEAD, "policy_sha256": "p"},
    "triage": {"tier": "DEEP", "fired": []},
    "proofs": [], "facts": [], "not_checked": [],
    "decisions": [{"id": "D1"}], "findings": [{"id": "F1"}], "abstentions": [{"id": "A1"}],
    "signoff_policy": {"demo_allow_author_signoff": False, "required_author_association": ["OWNER", "MEMBER", "COLLABORATOR"],
                       "agent_accounts_denied": ["claude"], "exclude_head_commit_authors": True},
}


def body(**kw):
    vals = {"head": HEAD, "ledger": "abcdef123456", "decision": "request_changes", "D1": "request_change", "F1": "valid", "A1": "defer"}
    vals.update(kw)
    return "/sign\n" + "\n".join(f"{k}: {v}" for k, v in vals.items())


class SignTests(unittest.TestCase):
    def test_valid_request_changes(self):
        r = sign.validate(body(), LEDGER, "reviewer", HEAD, "author")
        self.assertTrue(r["ok"], r["errors"])
        self.assertFalse(r["record"]["ai_counted_as_reviewer"])

    def test_author_cannot_sign(self):
        r = sign.validate(body(), LEDGER, "author", HEAD, "author")
        self.assertFalse(r["ok"])

    def test_bot_cannot_sign(self):
        r = sign.validate(body(), LEDGER, "github-actions[bot]", HEAD, "author")
        self.assertFalse(r["ok"])

    def test_stale_head_rejected(self):
        r = sign.validate(body(head="fffffff"), LEDGER, "reviewer", HEAD, "author")
        self.assertFalse(r["ok"])

    def test_short_head_prefix_rejected(self):
        r = sign.validate(body(head="1"), LEDGER, "reviewer", HEAD, "author")
        self.assertFalse(r["ok"])

    def test_duplicate_keys_rejected(self):
        r = sign.validate(body() + "\nD1: accept", LEDGER, "reviewer", HEAD, "author")
        self.assertFalse(r["ok"])

    def test_outsider_cannot_sign(self):
        r = sign.validate(body(), LEDGER, "drive-by", HEAD, "author", author_association="NONE")
        self.assertFalse(r["ok"])

    def test_commit_author_cannot_sign(self):
        r = sign.validate(body(), LEDGER, "pusher", HEAD, "author", head_commit_authors=["author", "pusher"])
        self.assertFalse(r["ok"])

    def test_agent_account_cannot_sign(self):
        r = sign.validate(body(), LEDGER, "Claude", HEAD, "author")
        self.assertFalse(r["ok"])

    def test_ledger_for_other_pr_rejected(self):
        r = sign.validate(body(), LEDGER, "reviewer", HEAD, "author", pr_number=2)
        self.assertFalse(r["ok"])

    def test_unresolved_item_rejected(self):
        r = sign.validate(body(A1="UNRESOLVED"), LEDGER, "reviewer", HEAD, "author")
        self.assertFalse(r["ok"])

    def test_cannot_approve_with_requested_change(self):
        r = sign.validate(body(decision="approve"), LEDGER, "reviewer", HEAD, "author")
        self.assertFalse(r["ok"])

    def test_review_state_must_match_decision(self):
        r = sign.validate(body(), LEDGER, "reviewer", HEAD, "author", review_state="APPROVED")
        self.assertFalse(r["ok"])
        r = sign.validate(body(), LEDGER, "reviewer", HEAD, "author", review_state="CHANGES_REQUESTED")
        self.assertTrue(r["ok"], r["errors"])

    def test_approve_when_consistent(self):
        r = sign.validate(body(decision="approve", D1="accept", F1="invalid", A1="accept_risk"), LEDGER, "reviewer", HEAD, "author")
        self.assertTrue(r["ok"], r["errors"])


class UnknownIsNeverAPassTests(unittest.TestCase):
    def run_eval(self, outcomes, expect="all_pass"):
        runs = {"r": {"meta": {}, "tests": [{"name": f"T{i}", "outcome": o, "message": ""} for i, o in enumerate(outcomes)]}}
        return evidence.evaluate([{"id": "P", "run": "r", "filter": ".", "expect": expect, "grade": "MEASURED"}], runs)[0]

    def test_timeout_is_not_a_pass(self):
        self.assertEqual(self.run_eval(["Passed", "Timeout"])["result"], "UNSUPPORTED")

    def test_no_tests_is_not_a_pass(self):
        self.assertEqual(self.run_eval([])["result"], "UNSUPPORTED")

    def test_missing_run_is_unsupported(self):
        p = evidence.evaluate([{"id": "P", "run": "absent", "filter": ".", "expect": "all_pass", "grade": "MEASURED"}], {})[0]
        self.assertEqual(p["result"], "UNSUPPORTED")

    def test_all_pass_holds(self):
        self.assertEqual(self.run_eval(["Passed", "Passed"])["result"], "HOLDS")

    def test_empty_diff_is_not_light(self):
        self.assertNotEqual(triage.run([], POLICY, {}).tier, "LIGHT")

    def test_binary_change_is_not_light(self):
        f = diffparse.FileDiff("lib/native.dll", "M", [], binary=True)
        self.assertNotEqual(triage.run([f], POLICY, {}).tier, "LIGHT")

    def test_whitespace_inside_string_is_not_light(self):
        t = triage.run([fd("src/Run.cs", ['var c = "rm -rf /tmp /x";'], ['var c = "rm -rf /tmp/x";'])], POLICY, {})
        self.assertNotEqual(t.tier, "LIGHT")

    def test_yaml_indentation_is_not_light(self):
        t = triage.run([fd("deploy/app.yaml", ["  replicas: 3"], ["replicas: 3"])], POLICY, {})
        self.assertNotEqual(t.tier, "LIGHT")


class EscapingTests(unittest.TestCase):
    def test_md_escape_neutralises_links_mentions_html(self):
        out = render_md.md_escape("<img src=x> [click](http://evil) @org/admins #12\n[x]: http://evil")
        for bad in ("<img", "](", "@org", "#12", "\n", "http://"):
            self.assertNotIn(bad, out)

    def test_code_span_cannot_break_out(self):
        self.assertEqual(render_md.code("a`b").count("`"), 2)


class EndToEndTriageTests(unittest.TestCase):
    """Whole-repo diff: a PR touching CI or policy outside sample/ must be DEEP, never LIGHT."""

    def git(self, *a):
        return subprocess.run(["git", *a], cwd=self.d, check=True, capture_output=True, text=True).stdout.strip()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = self.tmp.name
        self.git("init", "-q")
        self.git("config", "user.email", "t@example.invalid")
        self.git("config", "user.name", "t")
        os.makedirs(os.path.join(self.d, "sample/docs"))
        os.makedirs(os.path.join(self.d, ".github/workflows"))
        Path(os.path.join(self.d, "sample/docs/a.md")).write_text("hello\n")
        Path(os.path.join(self.d, ".github/workflows/sign.yml")).write_text("on: push\n")
        self.git("add", "-A")
        self.git("commit", "-qm", "base")
        self.base = self.git("rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def build(self):
        head = self.git("rev-parse", "HEAD")
        return ledger.build(repo=self.d, base=self.base, head=head, prefix="sample/", policy=POLICY,
                            review_input={"requirement_id": "X"}, evidence_dir=Path(self.d, "none"), provenance=None, pr={})

    def test_workflow_change_is_deep(self):
        Path(os.path.join(self.d, ".github/workflows/sign.yml")).write_text("on: push\njobs: {}\n")
        self.git("commit", "-qam", "edit workflow")
        L = self.build()
        self.assertEqual(L["triage"]["tier"], "DEEP")
        self.assertIn("R-POLICY-FILES", [f["rule"] for f in L["triage"]["fired"]])

    def test_docs_only_inside_sample_is_light(self):
        Path(os.path.join(self.d, "sample/docs/a.md")).write_text("hello world\n")
        self.git("commit", "-qam", "docs")
        self.assertEqual(self.build()["triage"]["base_tier"], "LIGHT")


if __name__ == "__main__":
    unittest.main()
