"""Score an image pipeline against test_suite/ground_truth.json.

A pipeline is a function that takes image bytes and returns the slab fields.
The return value can be a dict, a JSON string, or any object with model_dump().
"""

import json
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRUTH_PATH = ROOT / "test_suite" / "ground_truth.json"
RESULTS_DIR = ROOT / "test_suite" / "results"


def normalize(field: str, value) -> str:
    if field == "is_graded":
        if isinstance(value, str):
            return "true" if value.strip().lower() == "true" else "false"
        return "true" if bool(value) else "false"
    return " ".join(str(value or "").strip().casefold().split())


def as_fields(prediction) -> dict:
    if hasattr(prediction, "model_dump"):
        prediction = prediction.model_dump()
    elif isinstance(prediction, str):
        start = prediction.find("{")
        end = prediction.rfind("}")
        if start < 0 or end < start:
            return {}
        try:
            prediction = json.loads(prediction[start:end + 1])
        except json.JSONDecodeError:
            return {}
    return prediction if isinstance(prediction, dict) else {}


def evaluate_pipeline(name: str, predict, cases: list[dict] | None = None) -> dict:
    """Time predict() on each ground-truth photo and score the fields.

    predict(image_bytes) -> dict, JSON string, or a model with model_dump().
    The report is written to test_suite/results/<name>.json.
    """
    if cases is None:
        cases = json.loads(TRUTH_PATH.read_text())
    results = []
    for case in cases:
        
        image_path = ROOT / case["image_path"]
        error = ""
        started = time.perf_counter()
        meta = {}
        try:
            raw = predict(image_path.read_bytes())
            if isinstance(raw, tuple):
                raw, meta = raw
            prediction = as_fields(raw)
        except Exception as exc:
            prediction = {}
            error = str(exc)
        elapsed = round(time.perf_counter() - started, 3)
        expected = case["expected"]
        field_match = {
            field: normalize(field, prediction.get(field)) == normalize(field, expected.get(field))
            for field in expected
        }
        results.append({
            "id": case["id"],
            "category": case["category"],
            "seconds": elapsed,
            "correct": all(field_match.values()),
            "fields": field_match,
            "expected": expected,
            "predicted": {field: prediction.get(field, "") for field in expected},
            "error": error,
            "prompt_tokens": meta.get("prompt_tokens"),
            "answer_confidence": meta.get("answer_confidence"),
            "field_confidence": meta.get("field_confidence", {}),
        })
        print(f"{case['id']} {elapsed:.1f}s {'ok' if results[-1]['correct'] else 'miss'}", flush=True)
        _write_report(name, cases, results)

    return _write_report(name, cases, results)


def _write_report(name: str, cases: list[dict], results: list[dict]) -> dict:
    times = [row["seconds"] for row in results]
    fields = list(cases[0]["expected"])
    by_category = {}
    for row in results:
        bucket = by_category.setdefault(row["category"], {"correct": 0, "total": 0})
        bucket["total"] += 1
        bucket["correct"] += int(row["correct"])
    for bucket in by_category.values():
        bucket["accuracy"] = round(bucket["correct"] / bucket["total"], 3)
    report = {
        "model": name,
        "images": len(results),
        "record_accuracy": round(sum(row["correct"] for row in results) / len(results), 3),
        "field_accuracy": {
            field: round(sum(row["fields"][field] for row in results) / len(results), 3)
            for field in fields
        },
        "category_accuracy": by_category,
        "seconds": {
            "total": round(sum(times), 3),
            "mean": round(statistics.mean(times), 3),
            "median": round(statistics.median(times), 3),
        },
        "results": results,
    }
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / f"{name}.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
