"""Fold externally-produced Unlimited-OCR outputs into the harness.

Unlimited-OCR runs on a separate GPU (Colab/Kaggle, see the Plan-B notebook).
That run saves `{test_id}_output.md` files plus an optional `_unlimited_runlog.csv`
(test_id,input_file,latency_sec,status). Drop those into `outputs/unlimited_ocr/`,
then run this script: it appends `unlimited_ocr` rows to `results/run_log.csv` so
`init_metrics.py` + `generate_report.py` include it as a 4th model.

Usage:
    python scripts/import_unlimited_ocr.py
"""

from __future__ import annotations

import argparse
import csv
import os
import re
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_LOG_COLUMNS = [
    "timestamp", "test_id", "input_file", "model",
    "output_file", "latency_sec", "status", "error",
]


def _test_id(name: str) -> str:
    m = re.match(r"(T\d+)", os.path.basename(name), flags=re.IGNORECASE)
    return m.group(1).upper() if m else os.path.splitext(os.path.basename(name))[0]


def _read_csv(path: str) -> list[dict]:
    if not os.path.isfile(path):
        return []
    with open(path, "r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def import_outputs(out_dir: str, run_log: str) -> int:
    sidecar = {r["test_id"]: r for r in _read_csv(os.path.join(out_dir, "_unlimited_runlog.csv"))}

    new_rows = []
    for fname in sorted(os.listdir(out_dir)):
        if not fname.endswith("_output.md"):
            continue
        tid = _test_id(fname)
        meta = sidecar.get(tid, {})
        new_rows.append({
            "timestamp": meta.get("timestamp") or datetime.now().isoformat(timespec="seconds"),
            "test_id": tid,
            "input_file": meta.get("input_file", ""),
            "model": "unlimited_ocr",
            "output_file": os.path.join("outputs", "unlimited_ocr", fname),
            "latency_sec": meta.get("latency_sec", ""),
            "status": meta.get("status", "success"),
            "error": meta.get("error", ""),
        })

    if not new_rows:
        raise FileNotFoundError(
            f"No *_output.md files in '{out_dir}'. Download them from the Plan-B "
            f"notebook first."
        )

    # Keep other models' rows; replace any previous unlimited_ocr rows.
    existing = [r for r in _read_csv(run_log) if r.get("model") != "unlimited_ocr"]
    combined = existing + new_rows

    os.makedirs(os.path.dirname(run_log) or ".", exist_ok=True)
    with open(run_log, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=RUN_LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(combined)
    return len(new_rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Import Unlimited-OCR outputs.")
    parser.add_argument("--out-dir", default="outputs/unlimited_ocr")
    parser.add_argument("--run-log", default="results/run_log.csv")
    args = parser.parse_args(argv)
    n = import_outputs(args.out_dir, args.run_log)
    print(f"Imported {n} unlimited_ocr row(s) into {args.run_log}.")
    print("Next: python scripts/init_metrics.py && python scripts/generate_report.py")


if __name__ == "__main__":
    main()
