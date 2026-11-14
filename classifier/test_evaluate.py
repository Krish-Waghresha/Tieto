import unittest

from evaluate import measure


class EvaluationTests(unittest.TestCase):
    def analysis(self, labels):
        return {"mode": "PA-only", "nodes": [{"name": name, "color": color, "change": "modified"} for name, color in labels.items()]}

    def test_false_green_uses_green_predictions_as_denominator(self):
        result = measure(self.analysis({"first": "green", "second": "green", "third": "gray"}), {"first": "red", "second": "green", "third": "amber"})
        self.assertEqual(result["false_green_count"], 1)
        self.assertEqual(result["false_green_fraction_of_green"], 0.5)

    def test_no_green_is_not_reported_as_perfect_green_safety(self):
        result = measure(self.analysis({"first": "gray"}), {"first": "red"})
        self.assertIsNone(result["false_green_fraction_of_green"])
        self.assertEqual(result["gray_fraction"], 1)

    def test_missing_reference_labels_are_not_silently_ignored(self):
        with self.assertRaises(ValueError):
            measure(self.analysis({"first": "green"}), {})

    def test_duplicate_block_names_cannot_hide_an_evaluation_case(self):
        analysis = self.analysis({"overload": "green"})
        analysis["nodes"].append({"name": "overload", "color": "red", "change": "modified"})
        with self.assertRaisesRegex(ValueError, "Ambiguous"):
            measure(analysis, {"overload": "green"})


if __name__ == "__main__":
    unittest.main()