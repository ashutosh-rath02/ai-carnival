"""Generate the Markdown comparison report from the scoring sheet.

Reads ``results/metrics.csv`` (with your manual 0-5 scores filled in) and writes
``results/final_report.md``: a results table, winner per test case, average score
per model, the best overall model, and editable placeholders for the qualitative
insights you add by hand.

Usage:
    python scripts/generate_report.py
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict
from datetime import date

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from evaluators.scoring_template import SCORE_SCALE, overall_score  # noqa: E402

REPORT_TITLE = "# AI OCR Field Test: 3 OCR/Document AI Tools on 10 Messy Documents"

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


def _read_metrics(path: str) -> list[dict]:
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"No metrics file at '{path}'. Run scripts/init_metrics.py first."
        )
    with open(path, "r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _num(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _fmt(value) -> str:
    return "-" if value is None else f"{value:.2f}"


def _row_overall(row: dict):
    """Use a manually entered overall_score if present, else compute it."""
    manual = _num(row.get("overall_score"))
    if manual is not None:
        return manual
    return overall_score(
        row.get("text_score"),
        row.get("field_score"),
        row.get("table_score"),
        row.get("hallucination_score"),
    )


def build_report(rows: list[dict], insights_path: str | None = None) -> str:
    models = sorted({r["model"] for r in rows if r.get("model")})
    test_ids = _sorted_test_ids({r["test_id"] for r in rows if r.get("test_id")})

    overalls = {(r["test_id"], r["model"]): _row_overall(r) for r in rows}

    lines: list[str] = []
    lines.append(REPORT_TITLE)
    lines.append("")
    lines.append(f"_Generated {date.today().isoformat()}._")
    lines.append("")

    # Experiment summary
    lines.append("## Experiment summary")
    lines.append("")
    lines.append(
        "A practical field test comparing OCR / document-AI tools on messy "
        "real-world documents. Each model ran over the same set of documents; "
        "raw outputs were scored by hand on a 0-5 scale across four dimensions."
    )
    lines.append("")

    # Models tested
    lines.append("## Models tested")
    lines.append("")
    for model in models:
        lines.append(f"- `{model}`")
    lines.append("")

    # Test cases
    lines.append("## Test cases")
    lines.append("")
    lines.append("| ID | Case | Input file |")
    lines.append("| --- | --- | --- |")
    seen_files = {}
    for r in rows:
        seen_files.setdefault(r["test_id"], r.get("input_file", ""))
    for tid in test_ids:
        case = CASE_MAP.get(tid.upper(), "")
        lines.append(f"| {tid} | {case} | {seen_files.get(tid, '')} |")
    lines.append("")

    # Scoring method
    lines.append("## Scoring method")
    lines.append("")
    lines.append("Each output was scored 0-5 per dimension:")
    lines.append("")
    for value, meaning in SCORE_SCALE.items():
        lines.append(f"- **{value}** = {meaning}")
    lines.append("")
    lines.append(
        "Dimensions: text, field, table, hallucination (higher = hallucinated "
        "less). **Overall = average of the four.**"
    )
    lines.append("")

    # Results table
    lines.append("## Results")
    lines.append("")
    lines.append(
        "| Test | Model | Text | Field | Table | Halluc. | Latency (s) | Overall |"
    )
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for tid in test_ids:
        for r in [x for x in rows if x["test_id"] == tid]:
            lines.append(
                "| {tid} | {model} | {t} | {f} | {tb} | {h} | {lat} | {ov} |".format(
                    tid=tid,
                    model=r["model"],
                    t=_fmt(_num(r.get("text_score"))),
                    f=_fmt(_num(r.get("field_score"))),
                    tb=_fmt(_num(r.get("table_score"))),
                    h=_fmt(_num(r.get("hallucination_score"))),
                    lat=_fmt(_num(r.get("latency_sec"))),
                    ov=_fmt(overalls[(tid, r["model"])]),
                )
            )
    lines.append("")

    # Winner by test case
    lines.append("## Winner by test case")
    lines.append("")
    lines.append("| Test | Case | Winner | Overall |")
    lines.append("| --- | --- | --- | --- |")
    for tid in test_ids:
        winner, best = _best_for_test(tid, models, overalls)
        lines.append(
            f"| {tid} | {CASE_MAP.get(tid.upper(), '')} | "
            f"{winner or 'TBD (score first)'} | {_fmt(best)} |"
        )
    lines.append("")

    # Average score by model
    lines.append("## Average score by model")
    lines.append("")
    lines.append("| Model | Avg overall | Avg latency (s) | Docs scored |")
    lines.append("| --- | --- | --- | --- |")
    model_avgs = {}
    for model in models:
        avg_overall, avg_latency, n_scored = _model_aggregate(model, rows, overalls)
        model_avgs[model] = avg_overall
        lines.append(
            f"| {model} | {_fmt(avg_overall)} | {_fmt(avg_latency)} | {n_scored} |"
        )
    lines.append("")

    # Best overall model
    lines.append("## Best overall model")
    lines.append("")
    best_model, best_avg = _best_overall_model(model_avgs)
    if best_model is None:
        lines.append("_TBD — fill in scores in `results/metrics.csv`, then regenerate._")
    else:
        lines.append(f"**{best_model}** with an average overall score of "
                     f"**{best_avg:.2f}**.")
    lines.append("")

    # Qualitative insights: use results/insights.md if present so hand-written
    # verdicts survive regeneration; otherwise fall back to editable placeholders.
    insights = _read_insights(insights_path)
    if insights:
        lines.append(insights.rstrip())
        lines.append("")
    else:
        lines.append("## Most Surprising Result")
        lines.append("")
        lines.append("TODO: Add the most surprising result from manual review.")
        lines.append("")
        lines.append("## Worst Failure")
        lines.append("")
        lines.append("TODO: Add the worst failure case with screenshot reference.")
        lines.append("")
        lines.append("## Practical Verdict")
        lines.append("")
        lines.append("TODO: Add final takeaway.")
        lines.append("")

    return "\n".join(lines)


def _read_insights(path: str | None) -> str | None:
    if not path or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _sorted_test_ids(ids) -> list[str]:
    """Sort T-prefixed ids numerically (T2 before T10); others alphabetically."""
    def key(tid):
        if tid and tid[0].upper() == "T" and tid[1:].isdigit():
            return (0, int(tid[1:]))
        return (1, tid)

    return sorted(ids, key=key)


def _best_for_test(tid, models, overalls):
    best_model, best_score = None, None
    for model in models:
        score = overalls.get((tid, model))
        if score is None:
            continue
        if best_score is None or score > best_score:
            best_model, best_score = model, score
    return best_model, best_score


def _model_aggregate(model, rows, overalls):
    overall_vals, latency_vals = [], []
    for r in rows:
        if r["model"] != model:
            continue
        ov = overalls.get((r["test_id"], model))
        if ov is not None:
            overall_vals.append(ov)
        lat = _num(r.get("latency_sec"))
        if lat is not None:
            latency_vals.append(lat)
    avg_overall = round(sum(overall_vals) / len(overall_vals), 2) if overall_vals else None
    avg_latency = round(sum(latency_vals) / len(latency_vals), 2) if latency_vals else None
    return avg_overall, avg_latency, len(overall_vals)


def _best_overall_model(model_avgs):
    scored = {m: v for m, v in model_avgs.items() if v is not None}
    if not scored:
        return None, None
    best = max(scored, key=scored.get)
    return best, scored[best]


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Generate the comparison report.")
    parser.add_argument("--metrics", default="results/metrics.csv")
    parser.add_argument("--output", default="results/final_report.md")
    parser.add_argument(
        "--insights",
        default="results/insights.md",
        help="Optional Markdown file appended as the qualitative sections.",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    rows = _read_metrics(args.metrics)
    report = build_report(rows, insights_path=args.insights)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(report)
    print(f"Wrote report to {args.output} ({len(rows)} metric rows).")


if __name__ == "__main__":
    main()
