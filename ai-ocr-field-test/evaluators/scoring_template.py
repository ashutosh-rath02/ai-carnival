"""Scoring template + helpers.

Scoring is intentionally manual: you read each model's saved output and assign a
0-5 score per dimension. These helpers just document the scale and compute the
overall score the same way `generate_report.py` does, so numbers stay consistent.

Scale
-----
0 = failed / unusable
1 = mostly wrong
2 = partial extraction
3 = usable with human review
4 = mostly correct
5 = production-ready

Dimensions
----------
text_score          - quality of raw text extraction
field_score         - quality of structured field extraction (invoice no, totals, ...)
table_score         - how well table rows/structure were preserved
hallucination_score - higher = hallucinated LESS (5 = invented nothing)
"""

from __future__ import annotations

SCORE_DIMENSIONS = [
    "text_score",
    "field_score",
    "table_score",
    "hallucination_score",
]

SCORE_SCALE = {
    0: "failed / unusable",
    1: "mostly wrong",
    2: "partial extraction",
    3: "usable with human review",
    4: "mostly correct",
    5: "production-ready",
}


def overall_score(text_score, field_score, table_score, hallucination_score):
    """Average of the four scoring dimensions, ignoring blanks.

    Returns None if no dimension has been scored yet (so unscored rows stay blank
    instead of showing a misleading 0).
    """
    values = []
    for raw in (text_score, field_score, table_score, hallucination_score):
        if raw is None or raw == "":
            continue
        try:
            values.append(float(raw))
        except (TypeError, ValueError):
            continue
    if not values:
        return None
    return round(sum(values) / len(values), 2)
