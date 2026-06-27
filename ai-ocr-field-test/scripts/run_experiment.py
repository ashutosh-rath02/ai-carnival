"""Run the OCR field-test experiment.

Discovers documents in the input folder, runs the selected model runners over
each one, saves raw outputs per model, and writes a run log CSV with latency and
status for every (document, model) pair.

Usage:
    python scripts/run_experiment.py --models paddleocr vlm mistral_ocr
    python scripts/run_experiment.py --models paddleocr --limit 3
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from datetime import datetime

# Make the repo root importable when run as `python scripts/run_experiment.py`.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from runners import AVAILABLE_RUNNERS, get_runner  # noqa: E402
from runners.base import test_id_from_path  # noqa: E402
from runners.pdf_utils import SUPPORTED_EXTS  # noqa: E402

RUN_LOG_COLUMNS = [
    "timestamp",
    "test_id",
    "input_file",
    "model",
    "output_file",
    "latency_sec",
    "status",
    "error",
]


def discover_documents(input_dir: str, limit: int | None = None) -> list[str]:
    """Return sorted paths of supported documents in the input folder."""
    if not os.path.isdir(input_dir):
        return []
    files = [
        os.path.join(input_dir, name)
        for name in sorted(os.listdir(input_dir))
        if os.path.splitext(name)[1].lower() in SUPPORTED_EXTS
        and os.path.isfile(os.path.join(input_dir, name))
    ]
    return files[:limit] if limit else files


def _progress(iterable, total, desc):
    """Use tqdm if available, otherwise return the plain iterable."""
    try:
        from tqdm import tqdm

        return tqdm(iterable, total=total, desc=desc)
    except ImportError:
        return iterable


def run_experiment(models, input_dir, output_dir, metrics_path, limit=None):
    documents = discover_documents(input_dir, limit)
    if not documents:
        print(f"No supported documents found in '{input_dir}'. "
              f"Supported: {', '.join(sorted(SUPPORTED_EXTS))}")
        return

    print(f"Found {len(documents)} document(s). Models: {', '.join(models)}\n")

    os.makedirs(os.path.dirname(metrics_path) or ".", exist_ok=True)
    rows = []

    for model in models:
        model_out_dir = os.path.join(output_dir, model)
        try:
            runner = get_runner(model)
        except ValueError as exc:
            print(f"  [skip] {exc}")
            # Still log a failed row per document so the run log is complete.
            for doc in documents:
                rows.append(_row(doc, model, None, 0.0, "failed", str(exc)))
            continue

        print(f"== {model} ==")
        for doc in _progress(documents, total=len(documents), desc=model):
            result = runner.run(doc, model_out_dir)
            rows.append(
                _row(
                    doc,
                    model,
                    result.get("output_file"),
                    result.get("latency_sec", 0.0),
                    result.get("status", "failed"),
                    result.get("error"),
                )
            )
            status = result.get("status")
            mark = "ok " if status == "success" else "ERR"
            note = "" if status == "success" else f" -> {result.get('error')}"
            print(f"  [{mark}] {os.path.basename(doc)} "
                  f"({result.get('latency_sec', 0.0):.2f}s){note}")
        print()

    _write_run_log(metrics_path, rows)
    n_ok = sum(1 for r in rows if r["status"] == "success")
    print(f"Wrote {len(rows)} rows ({n_ok} success) to {metrics_path}")


def _row(input_file, model, output_file, latency_sec, status, error):
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "test_id": test_id_from_path(input_file),
        "input_file": os.path.basename(input_file),
        "model": model,
        "output_file": output_file or "",
        "latency_sec": f"{float(latency_sec):.3f}",
        "status": status,
        "error": error or "",
    }


def _write_run_log(metrics_path: str, rows: list[dict]) -> None:
    with open(metrics_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=RUN_LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the AI OCR field test.")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["paddleocr"],
        help=f"Runners to execute. Available: {', '.join(AVAILABLE_RUNNERS)}",
    )
    parser.add_argument("--input-dir", default="inputs")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--metrics", default="results/run_log.csv")
    parser.add_argument(
        "--limit", type=int, default=None, help="Only process the first N documents."
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    run_experiment(
        models=args.models,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        metrics_path=args.metrics,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
