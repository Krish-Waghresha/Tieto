import copy
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("classification_engine", ROOT / "engine.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
POLICY = json.loads((ROOT / "policy.json").read_text())


class EngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analysis = engine.extract(ROOT / "fixtures/order-flow/base", ROOT / "fixtures/order-flow/head")

    def node(self, suffix):
        return copy.deepcopy(next(node for node in self.analysis["nodes"] if node["name"].endswith(suffix)))

    def test_synthetic_oracle_is_met_without_becoming_engine_input(self):
        expected = json.loads((ROOT / "fixtures/order-flow/oracle.json").read_text())["expected"]
        actual = engine.classify(self.analysis, POLICY)
        labels = {node["name"]: node["color"] for node in actual["nodes"] if node["change"] == "modified"}
        self.assertEqual(labels, expected)
        self.assertEqual(actual["mode"], "PA-only")

    def test_calls_and_dynamic_target_are_derived(self):
        self.assertEqual(len(self.analysis["changedFiles"]), 4)
        self.assertEqual(len(self.analysis["edges"]), 6)
        self.assertTrue(any(edge["kind"] == "dynamic" for edge in self.analysis["edges"]))
        self.assertEqual(self.analysis["errors"], {"before": [], "after": []})

    def test_real_cfg_and_data_flow_exist(self):
        node = self.node("Pricing.Total")
        self.assertGreater(len(node["after"]["conditions"]), len(node["before"]["conditions"]))
        self.assertTrue(node["after"]["dataFlow"]["succeeded"])
        self.assertIn("subtotal", node["after"]["dataFlow"]["writes"])

    def test_removing_boundary_marker_cannot_downgrade_a_base_boundary(self):
        node = self.node("Access.CanSubmit")
        node["facts"]["protectedAfter"] = False
        self.assertEqual(engine.classify_node(node, POLICY)[0], "red")

    def test_model_cannot_turn_protected_or_unresolved_nodes_green(self):
        signals = {node["id"]: {"choice": "light", "confidence": 0.99, "probabilities": {"light": 0.99, "inspect": 0.005, "critical": 0.003, "unknown": 0.002}} for node in self.analysis["nodes"]}
        result = engine.classify(self.analysis, POLICY, signals, {"status": "executed", "testDouble": True})
        colors = {node["name"]: node["color"] for node in result["nodes"]}
        self.assertEqual(colors["HarborOrders.Access.CanSubmit"], "red")
        self.assertEqual(colors["HarborOrders.Shipping.Quote"], "gray")

    def test_model_can_escalate_requirement_conflict(self):
        node = self.node("Pricing.Total")
        signal = {"choice": "critical", "confidence": 0.95, "probabilities": {"critical": 0.95, "light": 0.01, "inspect": 0.03, "unknown": 0.01}}
        output = engine.classify(self.analysis, POLICY, {node["id"]: signal}, {"status": "executed", "testDouble": True})
        self.assertEqual(next(item for item in output["nodes"] if item["id"] == node["id"])["color"], "red")

    def test_incomplete_analysis_or_directives_block_green(self):
        for field, value in [("compilationComplete", False), ("hasDirectives", True), ("sourceSensitive", True)]:
            node = self.node("Receipt.Format")
            node["facts"][field] = value
            self.assertEqual(engine.classify_node(node, POLICY)[0], "gray")

    def test_green_candidate_inherits_changed_callee_attention(self):
        analysis = copy.deepcopy(self.analysis)
        receipt = next(node for node in analysis["nodes"] if node["name"].endswith("Receipt.Format"))
        pricing = next(node for node in analysis["nodes"] if node["name"].endswith("Pricing.Total"))
        analysis["edges"].append({"source": receipt["id"], "target": pricing["id"]})
        result = engine.classify(analysis, POLICY)
        actual = next(node for node in result["nodes"] if node["id"] == receipt["id"])
        self.assertEqual(actual["color"], "amber")
        self.assertEqual(actual["rule"], "dependency")

    def test_model_response_rejects_missing_or_invalid_answers(self):
        with self.assertRaises(ValueError):
            engine.parse_model_response({"answers": {}}, self.analysis)

    def test_model_adapter_parses_a_controlled_response_without_network(self):
        payload = engine.model_request(self.analysis, "Bulk order pricing")
        answer = {"type": "choice", "choice": "inspect", "confidence": 0.8,
                  "probabilities": {"light": 0.05, "inspect": 0.8, "critical": 0.1, "unknown": 0.05}}
        response = {"answers": {key: answer for key in payload["questions"]}}
        with mock.patch.dict(engine.os.environ, {"GEMINI_API_KEY": "test-only-placeholder"}), mock.patch.object(engine.urllib.request, "urlopen", return_value=io.StringIO(json.dumps(response))) as request:
            signals, metadata = engine.call_model(self.analysis, "Bulk order pricing")
        self.assertEqual(len(signals), 4)
        self.assertEqual(metadata["status"], "executed")
        self.assertEqual(request.call_args.args[0].get_method(), "POST")
        self.assertTrue(all(signal["choice"] == "inspect" for signal in signals.values()))

    def test_model_prompt_contains_source_facts_but_no_expected_colors(self):
        payload = engine.model_request(self.analysis, "Bulk pricing")
        self.assertEqual(len(payload["questions"]), 4)
        self.assertIn('"cfg"', payload["input"])
        self.assertNotIn("oracle", payload["input"])
        self.assertIn("untrusted", next(iter(payload["questions"].values()))["instructions"])

    def test_classification_does_not_mutate_extraction(self):
        original = copy.deepcopy(self.analysis)
        engine.classify(self.analysis, POLICY)
        self.assertEqual(original, self.analysis)

    def changed_fixture(self, modify):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "fixtures/order-flow/base", root / "base")
            shutil.copytree(ROOT / "fixtures/order-flow/head", root / "head")
            modify(root)
            return engine.classify(engine.extract(root / "base", root / "head"), POLICY)

    def test_string_whitespace_is_not_mechanical_whitespace(self):
        def modify(root):
            path = root / "head/Receipt.cs"
            path.write_text(path.read_text().replace('"Order "', '"Order  "'))
        result = self.changed_fixture(modify)
        receipt = next(node for node in result["nodes"] if node["name"].endswith("Receipt.Format"))
        self.assertEqual(receipt["color"], "amber")

    def test_source_directive_is_detected_not_ignored_as_trivia(self):
        def modify(root):
            path = root / "head/Receipt.cs"
            path.write_text("#nullable disable\n" + path.read_text())
        result = self.changed_fixture(modify)
        receipt = next(node for node in result["nodes"] if node["name"].endswith("Receipt.Format"))
        self.assertEqual(receipt["color"], "gray")

    def test_nameof_is_not_an_unresolved_runtime_call(self):
        def modify(root):
            path = root / "head/Receipt.cs"
            path.write_text(path.read_text().replace('"Order "', 'nameof(Order)'))
        result = self.changed_fixture(modify)
        receipt = next(node for node in result["nodes"] if node["name"].endswith("Receipt.Format"))
        self.assertEqual(receipt["after"]["unresolvedCalls"], [])
        self.assertEqual(receipt["color"], "amber")
        self.assertFalse(any(node.get("label") == "nameof" for node in result["nodes"]))

    def test_renaming_the_security_class_does_not_change_classification(self):
        def modify(root):
            for path in root.rglob("*.cs"):
                path.write_text(path.read_text().replace("class Access", "class TenantGate").replace("Access.CanSubmit", "TenantGate.CanSubmit"))
        result = self.changed_fixture(modify)
        self.assertEqual(result["errors"], {"before": [], "after": []})
        boundary = next(node for node in result["nodes"] if node["name"].endswith("TenantGate.CanSubmit"))
        self.assertEqual(boundary["color"], "red")

    def test_unscoped_declaration_changes_prevent_green(self):
        def modify(root):
            path = root / "head/Domain.cs"
            path.write_text(path.read_text() + "\npublic static class Defaults { public const int PackSize = 5; }\n")
        result = self.changed_fixture(modify)
        self.assertEqual(result["errors"], {"before": [], "after": []})
        self.assertTrue(any(node["kind"] == "file" and node["file"] == "Domain.cs" for node in result["nodes"]))
        receipt = next(node for node in result["nodes"] if node["name"].endswith("Receipt.Format"))
        self.assertEqual(receipt["color"], "gray")


class EvidenceEngineTests(unittest.TestCase):
    def setUp(self):
        self.analysis = {"baseHash": "base", "headHash": "head", "errors": {"before": [], "after": []}, "edges": [], "nodes": [
            {"id": "method", "file": "Parser.cs", "kind": "method", "change": "added", "facts": {"tokensEquivalent": False},
             "after": {"flowAvailable": True, "unresolvedCalls": [], "conditions": ["new behavior"]}}]}
        self.requirements = {"items": [{"id": "INV-1"}]}
        binding = {"base": "base", "head": "head", "requirements": engine.digest(self.requirements)}
        self.judgments = {"binding": binding, "origin": "authored-demo", "claims": [{"files": ["Parser.cs"],
            "requirements": ["INV-1"], "assessment": "supported", "confidence": 0.97, "summary": "Required parsing behavior is supported.", "tests": ["parse-boundary"]}]}
        self.evidence = {"binding": binding, "tests": {"parse-boundary": {"status": "passed", "covers": ["Parser.cs"], "requirements": ["INV-1"]}}}

    def result(self):
        return engine.classify_evidence(self.analysis, self.requirements, self.judgments, self.evidence)

    def test_substantive_new_behavior_can_be_green(self):
        result = self.result()
        self.assertEqual(result["nodes"][0]["color"], "green")
        self.assertEqual(result["mode"], "scripted-hybrid")
        self.assertFalse(result["nodes"][0]["model"]["calibrated"])

    def test_failed_check_overrides_high_confidence(self):
        self.evidence["tests"]["parse-boundary"]["status"] = "failed"
        self.assertEqual(self.result()["nodes"][0]["color"], "red")

    def test_missing_or_unrelated_check_blocks_green(self):
        self.evidence["tests"]["parse-boundary"]["covers"] = ["Unrelated.cs"]
        self.assertEqual(self.result()["nodes"][0]["color"], "gray")

    def test_unresolved_call_blocks_green(self):
        self.analysis["nodes"][0]["after"]["unresolvedCalls"] = ["provider.Tax"]
        self.assertEqual(self.result()["nodes"][0]["color"], "gray")

    def test_low_confidence_and_ambiguity_need_confirmation(self):
        self.judgments["claims"][0]["confidence"] = 0.70
        self.assertEqual(self.result()["nodes"][0]["color"], "amber")
        self.judgments["claims"][0]["assessment"] = "clarify"
        self.judgments["claims"][0]["confidence"] = 0.99
        self.assertEqual(self.result()["nodes"][0]["color"], "amber")

    def test_stale_evidence_is_rejected(self):
        self.evidence["binding"] = {**self.evidence["binding"], "head": "old"}
        with self.assertRaises(ValueError):
            self.result()

    def test_missing_ai_judgment_does_not_clear_behavior(self):
        self.judgments["claims"] = []
        self.assertEqual(self.result()["nodes"][0]["color"], "gray")

    def test_compilation_error_prevents_green(self):
        self.analysis["errors"]["after"] = ["Unresolved type"]
        self.assertEqual(self.result()["nodes"][0]["color"], "gray")

    def test_requirement_coverage_must_match(self):
        self.evidence["tests"]["parse-boundary"]["requirements"] = ["OTHER"]
        self.assertEqual(self.result()["nodes"][0]["color"], "gray")

    def test_declarations_require_explicit_review_scope(self):
        self.analysis["nodes"][0]["kind"] = "file"
        self.assertEqual(self.result()["nodes"][0]["color"], "gray")
        self.judgments["claims"][0]["coversDeclarations"] = True
        self.assertEqual(self.result()["nodes"][0]["color"], "green")

    def test_confidence_does_not_override_conflict(self):
        self.judgments["claims"][0].update(assessment="conflict", confidence=0.99)
        self.assertEqual(self.result()["nodes"][0]["color"], "red")

    def test_risky_callee_escalates_supported_caller(self):
        self.analysis["nodes"].append({"id": "external", "kind": "external", "change": "context"})
        self.analysis["edges"].append({"source": "method", "target": "external"})
        self.assertEqual(self.result()["nodes"][0]["color"], "amber")

    def test_input_is_not_mutated(self):
        original = copy.deepcopy(self.analysis)
        self.result()
        self.assertEqual(original, self.analysis)


if __name__ == "__main__":
    unittest.main()