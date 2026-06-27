"""Initialize the scoring sheet from the experiment run log.

Reads ``results/run_log.csv`` and writes ``results/metrics.csv`` with one row per
(test document, model). Latency is filled in automatically; the score columns are
left blank for you to fill in manually.

If a metrics.csv already exists, previously entered scores/notes are preserved by
default (matched on test_id + model), so re-running after a new experiment won't
wipe your manual work. Use --no-merge to start fresh.

Usage:
    python scripts/init_metrics.py
    python scripts/init_metrics.py --no-merge
"""

from __future__ import annotations

import argparse
import csv
import os

METRICS_COLUMNS = [
    "test_id",
    "case",
    "input_file",
    "model",
    "text_score",
    "field_score",
    "table_score",
    "hallucination_score",
    "latency_sec",
    "overall_score",
    "notes",
    "winner",
]

SCORE_COLUMNS = [
    "text_score",
    "field_score",
    "table_score",
    "hallucination_score",
    "overall_score",
    "notes",
    "winner",
]

# Maps the test id to a human-readable case description (PRD section 7).
CASE_MAP = {
    "T1": "Clean digital invoice",
    "T2": "Blurry invoice photo",
    "T3": "Rotated invoice",
    "T4": "Low-contrast scan",
    "T5": "Table-heavy invoice/packing list",
    "T6": "Long 10-page PDF",
    "T7": "Mixed text + image PDF",
    "T8": "Handwritten field on printed form",
    "T9": "Invoice with wrong total",
    "T10": "Multilingual document",
}


def _read_csv(path: str) -> list[dict]:
    if not os.path.isfile(path):
        return []
    with open(path, "r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def init_metrics(run_log_path: str, metrics_path: str, merge: bool = True) -> int:
    run_rows = _read_csv(run_log_path)
    if not run_rows:
        raise FileNotFoundError(
            f"No run log found at '{run_log_path}'. "
            f"Run scripts/run_experiment.py first."
        )

    # Preserve manual scores from an existing metrics file, keyed by
    # test_id+model+input_file. Including the filename means scores are only
    # carried over when it's the SAME document — switching inputs (e.g. synthetic
    # -> real) correctly leaves the score columns blank instead of mislabelling.
    preserved: dict[tuple, dict] = {}
    if merge:
        for row in _read_csv(metrics_path):
            key = (row.get("test_id", ""), row.get("model", ""), row.get("input_file", ""))
            preserved[key] = {col: row.get(col, "") for col in SCORE_COLUMNS}

    out_rows = []
    for row in run_rows:
        test_id = row.get("test_id", "")
        model = row.get("model", "")
        key = (test_id, model, row.get("input_file", ""))
        carried = preserved.get(key, {})
        out_rows.append(
            {
                "test_id": test_id,
                "case": CASE_MAP.get(test_id.upper(), ""),
                "input_file": row.get("input_file", ""),
                "model": model,
                "text_score": carried.get("text_score", ""),
                "field_score": carried.get("field_score", ""),
                "table_score": carried.get("table_score", ""),
                "hallucination_score": carried.get("hallucination_score", ""),
                "latency_sec": row.get("latency_sec", ""),
                "overall_score": carried.get("overall_score", ""),
                "notes": carried.get("notes", ""),
                "winner": carried.get("winner", ""),
            }
        )

    os.makedirs(os.path.dirname(metrics_path) or ".", exist_ok=True)
    with open(metrics_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=METRICS_COLUMNS)
        writer.writeheader()
        writer.writerows(out_rows)

    return len(out_rows)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Initialize the scoring sheet.")
    parser.add_argument("--run-log", default="results/run_log.csv")
    parser.add_argument("--metrics", default="results/metrics.csv")
    parser.add_argument(
        "--no-merge",
        action="store_true",
        help="Overwrite instead of preserving existing manual scores.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    count = init_metrics(args.run_log, args.metrics, merge=not args.no_merge)
    print(f"Wrote {count} row(s) to {args.metrics}.")
    print("Fill in the score columns (0-5), then run scripts/generate_report.py.")


if __name__ == "__main__":
    main()
