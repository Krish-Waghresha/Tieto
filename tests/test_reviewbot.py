"""Unit tests for the deterministic parts: verdict engine, C# facts, anti-phantom, sign rules."""
import json
import unittest
from pathlib import Path

from reviewbot import csharp_graph, diffparse, ledger, sign, triage

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


LEDGER = {
    "ledger_sha256": "abcdef1234567890",
    "requirement": {"id": "MP-1"},
    "pin": {"repo": "o/r", "pr": 1, "base": "b" * 40, "policy_sha256": "p"},
    "triage": {"tier": "DEEP", "fired": []},
    "proofs": [], "facts": [], "not_checked": [],
    "decisions": [{"id": "D1"}], "findings": [{"id": "F1"}], "abstentions": [{"id": "A1"}],
    "signoff_policy": {"demo_allow_author_signoff": False},
}
HEAD = "1234567" + "0" * 33


def body(**kw):
    vals = {"head": HEAD[:7], "ledger": "abcdef123456", "decision": "request_changes", "D1": "request_change", "F1": "valid", "A1": "defer"}
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


if __name__ == "__main__":
    unittest.main()
