"""Evaluate an already-produced analysis; reference labels are never classifier inputs."""
import argparse
import json
from pathlib import Path

COLORS = ("green", "amber", "red", "gray")


def measure(analysis, expected):
    changed = [node for node in analysis["nodes"] if node["change"] not in ("unchanged", "context")]
    actual = {node["name"]: node["color"] for node in changed}
    if len(actual) != len(changed):
        raise ValueError("Ambiguous block names; provide unique block identities before evaluating overloads")
    if set(actual) != set(expected):
        raise ValueError("Reference labels must cover exactly the changed analysis blocks")
    if any(color not in COLORS for color in list(actual.values()) + list(expected.values())):
        raise ValueError("Unknown attention label")
    total = len(expected)
    green = sum(color == "green" for color in actual.values())
    false_green = sum(actual[name] == "green" and expected[name] != "green" for name in expected)
    matrix = {label: {prediction: 0 for prediction in COLORS} for label in COLORS}
    for name, label in expected.items():
        matrix[label][actual[name]] += 1
    return {
        "mode": analysis["mode"],
        "blocks": total,
        "matching_labels": sum(actual[name] == label for name, label in expected.items()),
        "green_predictions": green,
        "false_green_count": false_green,
        "false_green_fraction_of_green": false_green / green if green else None,
        "gray_fraction": sum(color == "gray" for color in actual.values()) / total if total else None,
        "lighter_review_fraction": green / total if total else None,
        "confusion_matrix_expected_then_predicted": matrix,
        "mismatches": [{"block": name, "expected": expected[name], "actual": actual[name]} for name in expected if expected[name] != actual[name]],
        "limit": "Agreement on supplied labels only. Green fraction is not measured time saved. No prediction of production safety.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--analysis", type=Path, required=True)
    parser.add_argument("--labels", type=Path, required=True)
    args = parser.parse_args()
    labels = json.loads(args.labels.read_text())
    output = measure(json.loads(args.analysis.read_text()), labels["expected"])
    output["reference_purpose"] = labels.get("purpose", "Unspecified; not assumed to be independent")
    print(json.dumps(output, indent=2))