import unittest
from unittest import mock
from types import SimpleNamespace

import github_review as github
import github_demo


def pr():
    return {"number": 2, "state": "open", "changed_files": 2,
        "base": {"sha": "a" * 40, "ref": github.BASE_BRANCH, "repo": {"full_name": github.REPOSITORY}},
        "head": {"sha": "b" * 40, "ref": github.HEAD_BRANCH, "repo": {"full_name": github.REPOSITORY}}}


def analysis():
    return {"mode": "PA-only", "tool": {"version": "4.12"}, "nodes": [
        {"id": "first", "label": "Access.Check", "kind": "method", "color": "red", "change": "modified", "reason": "Boundary changed", "rule": "boundary", "file": "Access.cs", "after": {"line": 4, "endLine": 8}},
        {"id": "second", "label": "Receipt.Format", "kind": "method", "color": "green", "change": "modified", "reason": "Whitespace only", "rule": "whitespace", "file": "Receipt.cs", "after": {"line": 2, "endLine": 7}},
    ], "edges": [{"source": "first", "target": "second", "change": "unchanged"}]}


class GitHubReviewTests(unittest.TestCase):
    def test_only_transient_reads_are_retried(self):
        timeout = SimpleNamespace(returncode=1, stdout="", stderr="TLS handshake timeout")
        success = SimpleNamespace(returncode=0, stdout='{"ok": true}', stderr="")
        with mock.patch.object(github.subprocess, "run", side_effect=[timeout, success]) as command:
            self.assertEqual(github.api("repos/test/read"), {"ok": True})
            self.assertEqual(command.call_count, 2)
        with mock.patch.object(github.subprocess, "run", return_value=timeout) as command:
            with self.assertRaises(RuntimeError):
                github.api("repos/test/write", method="POST", body={})
            self.assertEqual(command.call_count, 1)

    def test_graph_preserves_colors_with_opaque_mermaid_ids(self):
        diagram = github.mermaid(analysis())
        self.assertIn('n0["Access.Check<br/>Human attention"]:::red', diagram)
        self.assertIn("n0 --> n1", diagram)
        self.assertIn("classDef green", diagram)

    def test_repository_names_cannot_inject_mermaid_syntax(self):
        data = analysis()
        data["nodes"][0]["label"] = 'Bad"]\nclick n0 "javascript:bad"\n```<script>'
        diagram = github.mermaid(data)
        self.assertNotIn("```", diagram)
        self.assertNotIn('<script>', diagram)
        self.assertNotIn('\nclick', diagram)

    def test_comment_is_crisp_and_does_not_claim_model_execution(self):
        body = github.render_comment(pr(), analysis(), "key")
        self.assertIn("```mermaid", body)
        self.assertIn("PA-only; model not run", body)
        self.assertIn("not merge approval", body)
        self.assertLess(len(body.split()), 145)
        self.assertIn("Open interactive playground", body)
        self.assertIn("local demo", body)

    def test_playground_link_is_bound_to_pr_and_analysis(self):
        with mock.patch.dict(github.os.environ, {"EARNED_PLAYGROUND_URL": "http://127.0.0.1:5174"}):
            url, local = github.playground_link(pr(), "result-hash")
        self.assertEqual(url, "http://127.0.0.1:5174/pr-2/result-hash/index.html")
        self.assertTrue(local)

    def test_playground_rejects_unsafe_or_credentialed_urls(self):
        for value in ("javascript:alert(1)", "https://user:secret@example.com", "https://example.com/?token=secret"):
            with mock.patch.dict(github.os.environ, {"EARNED_PLAYGROUND_URL": value}), self.assertRaises(ValueError):
                github.playground_link(pr(), "key")

    def test_visual_update_does_not_duplicate_inline_findings(self):
        comments = [{"path": "Access.cs", "line": 8, "body": "Attention", "side": "RIGHT"}]
        previous = [{"path": "Access.cs", "line": 8, "body": "Attention", "commit_id": "b" * 40, "user": {"login": "owner"}}]
        self.assertEqual(github.unpublished_annotations(comments, previous, "b" * 40, "owner"), [])
        self.assertEqual(github.unpublished_annotations(comments, previous, "c" * 40, "owner"), comments)

    def test_only_important_changed_methods_get_inline_comments(self):
        files = [{"filename": "Access.cs", "patch": "@@ -4,2 +4,3 @@\n old\n-old\n+new\n+extra"}]
        comments, skipped = github.annotations(analysis(), files)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0]["line"], 5)
        self.assertEqual(skipped, [])

    def test_missing_diff_anchor_is_not_fabricated(self):
        comments, skipped = github.annotations(analysis(), [])
        self.assertEqual(comments, [])
        self.assertEqual(skipped, ["Access.Check"])

    def test_stale_base_or_head_cannot_be_published(self):
        changed = pr()
        changed["head"]["sha"] = "c" * 40
        with self.assertRaisesRegex(ValueError, "changed during"):
            github.ensure_current(pr(), changed)

    def test_unrelated_demo_or_fork_is_not_processed(self):
        changed = pr()
        changed["head"]["ref"] = "demo/issue-2283"
        with self.assertRaises(ValueError):
            github.validate_pr(changed)

    def test_tree_path_traversal_is_rejected_before_writing(self):
        def api(endpoint):
            return {"tree": [{"path": "../escape.cs", "type": "blob", "mode": "100644", "sha": "x"}]}
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            github.read_snapshot("a" * 40, None, api)

    def test_demo_setup_never_overwrites_partial_branches(self):
        def api(endpoint, **options):
            self.assertNotIn("method", options)
            if endpoint.endswith("/earned-review-demo"):
                return {"private": True}
            return [{"ref": "refs/heads/" + github.BASE_BRANCH, "object": {"sha": "a" * 40}}]
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            github_demo.prepare(api)

    def test_demo_setup_does_not_add_an_oracle_or_workflows(self):
        trees = []
        def api(endpoint, **options):
            if endpoint.endswith("/earned-review-demo"):
                return {"private": True}
            if "matching-refs" in endpoint or "/pulls?" in endpoint:
                return []
            if endpoint.endswith("/git/trees"):
                trees.append(options["body"]["tree"])
                return {"sha": "tree"}
            if endpoint.endswith("/git/commits"):
                return {"sha": "commit"}
            if endpoint.endswith("/pulls"):
                return {"number": 2, "html_url": "https://github.com/example/pull/2"}
            return {}
        github_demo.prepare(api)
        self.assertEqual(len(trees), 2)
        for tree in trees:
            self.assertEqual(len(tree), 8)
            self.assertFalse(any("oracle" in item["path"] or ".github" in item["path"] for item in tree))


class InvoicePublicationTests(unittest.TestCase):
    def test_invoice_tree_excludes_generated_evidence_and_keeps_the_expected_diff(self):
        base, head = github_demo.invoice_contents()
        changed = {path for path in base.keys() | head.keys() if base.get(path) != head.get(path)}
        self.assertEqual(len(changed), 15)
        self.assertEqual(sum(len(head[path].splitlines()) for path in changed), 1618)
        self.assertTrue(all(path.endswith(".cs") for path in changed))
        self.assertFalse(any("judgments" in path or "analysis.json" in path or "bin/" in path for path in head))
        self.assertIn("src/*.cs", head["InvoiceImport.csproj"])
        self.assertNotIn("base/*.cs", head["InvoiceImport.csproj"])
        self.assertNotIn("not connected yet", head["README.md"])

    def test_remote_invoice_tree_must_match_exactly(self):
        contents = {"src/Example.cs": "class Example {}\n"}
        tree = {"tree": [{"path": path, "mode": "100644", "type": "blob", "sha": github_demo.blob_sha(text)} for path, text in contents.items()]}
        github_demo.verify_invoice_tree(contents, tree)
        tree["tree"][0]["sha"] = "wrong"
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            github_demo.verify_invoice_tree(contents, tree)

    def test_invoice_publisher_refuses_public_destination(self):
        with self.assertRaisesRegex(ValueError, "private"):
            github_demo.prepare_invoice(lambda endpoint: {"private": False})

    def test_invoice_comment_labels_authored_confidence_and_pins_sources(self):
        data = {"reviewKey": "key", "nodes": [{"id": "reader", "file": "Reader.cs"}, {"id": "writer", "file": "Writer.cs"}],
            "edges": [{"source": "reader", "target": "writer"}]}
        summary = {"modules": [{"file": "Reader.cs", "color": "green", "confidence": 0.97, "reason": "Bounded checks pass."},
            {"file": "Writer.cs", "color": "red", "confidence": 0.08, "reason": "Retry duplicates an invoice."}],
            "diff": {"added": 1618, "files": 15}, "checks": {"passed": 87, "failed": 1}, "methodColors": {"green": 17, "amber": 6, "red": 1, "gray": 1}}
        body = github_demo.invoice_comment({"head": {"sha": "b" * 40}}, data, summary)
        self.assertIn("authored demo inputs", body)
        self.assertIn("17 green / 6 amber / 1 red / 1 gray", body)
        self.assertIn("n0 --> n1", body)
        self.assertIn("/blob/" + "b" * 40 + "/src/Reader.cs", body)
        self.assertNotIn("127.0.0.1", body)
        linked = github_demo.invoice_comment({"head": {"sha": "b" * 40}}, data, summary, "http://127.0.0.1:5174/pr-3/key/index.html")
        self.assertIn("Open interactive review", linked)
        self.assertIn("<summary>Provenance</summary>", linked)
        self.assertNotIn("authored demo inputs", linked.split("<details>")[0])


if __name__ == "__main__":
    unittest.main()