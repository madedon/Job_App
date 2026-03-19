"""
Job Filter Benchmark -- Measures prescreening filter accuracy against labeled outcomes.

Usage:
    python tools/job_filter_benchmark.py
    python tools/job_filter_benchmark.py --verbose
"""
import sys, os, json, re, argparse
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prescreening_filter import prescreen

LABELED_DATA = Path(__file__).resolve().parent.parent / ".tmp" / "job_filter_labeled_dataset.json"


def load_labeled_data():
    with open(LABELED_DATA, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["rows"]


def run_benchmark(rows, verbose=False):
    tp = tn = fp = fn = skipped_unknown = 0
    details = []

    for row in rows:
        if row["label"] == "UNKNOWN":
            skipped_unknown += 1
            continue
        result = prescreen(jd_text=row["jd_text"], company=row["company"],
                          role=row["role"], location=row["location"])
        predicted = result["decision"]
        actual = row["label"]
        if predicted == "PROCEED" and actual == "PROCEED": tp += 1; mark = "TP"
        elif predicted == "AUTO_SKIP" and actual == "AUTO_SKIP": tn += 1; mark = "TN"
        elif predicted == "PROCEED" and actual == "AUTO_SKIP": fp += 1; mark = "FP"
        elif predicted == "AUTO_SKIP" and actual == "PROCEED": fn += 1; mark = "FN"
        else: mark = "??"
        details.append({"company": row["company"], "role": row["role"][:40],
                        "predicted": predicted, "actual": actual, "mark": mark,
                        "reason": result.get("reason", ""), "status": row["status"]})

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / max(total, 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 0.001)
    filter_rate = tn / max(tn + fp, 1)
    weighted_f1 = (1 + 4) * precision * recall / max((4 * precision) + recall, 0.001)

    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "total": total,
            "accuracy": accuracy, "precision": precision, "recall": recall,
            "f1": f1, "filter_rate": filter_rate, "weighted_f1": weighted_f1,
            "skipped_unknown": skipped_unknown, "details": details}


def main():
    parser = argparse.ArgumentParser(description="Job Filter Benchmark")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    rows = load_labeled_data()
    results = run_benchmark(rows, verbose=args.verbose)

    print("---")
    for k in ["accuracy", "precision", "recall", "f1", "weighted_f1", "filter_rate"]:
        print(f"{k}:         {results[k]:.6f}")
    print(f"true_positives:   {results['tp']}")
    print(f"true_negatives:   {results['tn']}")
    print(f"false_positives:  {results['fp']}")
    print(f"false_negatives:  {results['fn']}")
    print(f"total_evaluated:  {results['total']}")

    if results['fn'] > 0:
        print(f"\n  FALSE NEGATIVES (missed good jobs):")
        for d in results['details']:
            if d['mark'] == 'FN':
                print(f"    {d['company']}: {d['role']} -> filter said SKIP because: {d['reason']}")

    if args.verbose:
        print(f"\n  ALL PREDICTIONS:")
        for d in results['details']:
            marker = {"TP": "OK ", "TN": "OK ", "FP": "FP!", "FN": "FN!"}[d['mark']]
            print(f"    [{marker}] {d['company'][:20]:<20} | {d['role'][:35]:<35} | pred={d['predicted']:<10} actual={d['actual']:<10}")


if __name__ == "__main__":
    main()
