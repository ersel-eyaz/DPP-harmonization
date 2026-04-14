from __future__ import annotations

from collections import Counter, defaultdict

from evaluation_cases import EXAMPLE_EVALUATION_CASES
from harmonizer import DataHarmonizer


def evaluate_case(harmonizer: DataHarmonizer, case: EvaluationCase) -> dict:
    result = {
        "raw_label": case.raw_label,
        "entity_type": case.entity_type.value,
        "difficulty": case.difficulty,
        "expected": case.expected_canonical_concept.value if case.expected_canonical_concept else None,
        "predicted": None,
        "status": None,
        "resolution_method": None,
        "confidence": None,
    }

    batch_result = harmonizer.harmonize_dataset(
        [
            case.to_raw_observation()
        ]
    )

    if batch_result.dataset.records:
        record = batch_result.dataset.records[0]
        predicted = record.canonical_concept.value

        result["predicted"] = predicted
        result["resolution_method"] = record.resolution_method
        result["confidence"] = record.confidence

        if case.expected_canonical_concept is None:
            result["status"] = "false_positive"
        elif predicted == case.expected_canonical_concept.value:
            result["status"] = "correct"
        else:
            result["status"] = "wrong_concept"

        return result

    if case.expected_canonical_concept is None:
        result["status"] = "correct_unmapped"
    else:
        result["status"] = "missed"

    return result


def print_summary(results: list[dict]) -> None:
    status_counts = Counter(item["status"] for item in results)
    method_counts = Counter(
        item["resolution_method"] for item in results if item["resolution_method"] is not None
    )

    print()
    print("Overall summary")
    print(f" - total_cases: {len(results)}")
    print(f" - correct: {status_counts['correct']}")
    print(f" - correct_unmapped: {status_counts['correct_unmapped']}")
    print(f" - missed: {status_counts['missed']}")
    print(f" - wrong_concept: {status_counts['wrong_concept']}")
    print(f" - false_positive: {status_counts['false_positive']}")

    print()
    print("Resolution method counts")
    for method, count in sorted(method_counts.items()):
        print(f" - {method}: {count}")

    print()
    print("Difficulty breakdown")
    by_difficulty: dict[str, list[dict]] = defaultdict(list)
    for item in results:
        by_difficulty[item["difficulty"]].append(item)

    for difficulty, items in sorted(by_difficulty.items()):
        counts = Counter(item["status"] for item in items)
        print(f" - {difficulty}: total={len(items)}, correct={counts['correct']}, "
              f"correct_unmapped={counts['correct_unmapped']}, missed={counts['missed']}, "
              f"wrong_concept={counts['wrong_concept']}, false_positive={counts['false_positive']}")


def print_detailed_results(results: list[dict]) -> None:
    print()
    print("Detailed results")
    for item in results:
        print(
            f" - raw_label={item['raw_label']}, "
            f"entity_type={item['entity_type']}, "
            f"difficulty={item['difficulty']}, "
            f"expected={item['expected']}, "
            f"predicted={item['predicted']}, "
            f"status={item['status']}, "
            f"resolution_method={item['resolution_method']}, "
            f"confidence={item['confidence']}"
        )


def main() -> None:
    harmonizer = DataHarmonizer()
    results = [evaluate_case(harmonizer, case) for case in EXAMPLE_EVALUATION_CASES]

    print_summary(results)
    print_detailed_results(results)


if __name__ == "__main__":
    main()