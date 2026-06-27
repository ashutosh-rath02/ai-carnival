"""Build a single self-contained HTML viewer comparing the models.

Shows a leaderboard (avg quality + latency per model) and, per document, the
source next to each model's output with its 0-5 score, winner highlighted.
Output is one portable file: results/viewer.html (open it directly, no server).

Usage:
    python scripts/build_viewer.py
    python scripts/build_viewer.py --open
"""

from __future__ import annotations

import argparse
import base64
import csv
import html
import io
import json
import os
import sys
from collections import defaultdict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

MODEL_OUTPUTS = {
    "paddleocr": ("outputs/paddleocr", "{tid}_output.txt", "text"),
    "vlm": ("outputs/vlm", "{tid}_output.json", "json"),
    "mistral_ocr": ("outputs/mistral_ocr", "{tid}_output.md", "text"),
    "unlimited_ocr": ("outputs/unlimited_ocr", "{tid}_output.md", "text"),
}

DISPLAY = {
    "vlm": "VLM · Gemini 3.5 / GPT-5.5",
    "mistral_ocr": "Mistral OCR",
    "unlimited_ocr": "Unlimited-OCR",
    "paddleocr": "PaddleOCR",
}


def disp(model: str) -> str:
    return DISPLAY.get(model, model)


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _score_class(v):
    if v is None:
        return "s-na"
    if v >= 4.5:
        return "s5"
    if v >= 3.5:
        return "s4"
    if v >= 2.5:
        return "s3"
    if v >= 1.5:
        return "s2"
    return "s1"


def _img_data_uri(input_path: str, max_w: int = 460) -> str | None:
    try:
        from PIL import Image
    except ImportError:
        return None
    ext = os.path.splitext(input_path)[1].lower()
    img = None
    try:
        if ext in (".png", ".jpg", ".jpeg"):
            img = Image.open(input_path).convert("RGB")
        elif ext == ".pdf":
            from runners.pdf_utils import render_pdf_to_images

            pages = render_pdf_to_images(input_path, dpi=120)
            img = pages[0] if pages else None
    except Exception:
        return None
    if img is None:
        return None
    if img.width > max_w:
        ratio = max_w / img.width
        img = img.resize((max_w, int(img.height * ratio)))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _find_input(fname: str, primary_dir: str) -> str | None:
    candidates = [primary_dir, "inputs_real", "inputs",
                  os.path.join(REPO_ROOT, "inputs_real"), os.path.join(REPO_ROOT, "inputs")]
    seen = set()
    for d in candidates:
        if not d or d in seen:
            continue
        seen.add(d)
        path = os.path.join(d, fname)
        if os.path.isfile(path):
            return path
    return None


def _read_output(tid: str, model: str) -> str:
    spec = MODEL_OUTPUTS.get(model)
    if not spec:
        return "(unknown model)"
    subdir, pattern, kind = spec
    path = os.path.join(REPO_ROOT, subdir, pattern.format(tid=tid))
    if not os.path.isfile(path):
        return "(no output saved)"
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    if kind == "json":
        try:
            return json.dumps(json.loads(raw), ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, ValueError):
            return raw
    return raw


def _read_metrics(path: str) -> list[dict]:
    if not os.path.isfile(path):
        return []
    with open(path, "r", newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_html(metrics_path: str, input_dir: str) -> str:
    rows = _read_metrics(metrics_path)
    models = sorted({r["model"] for r in rows if r.get("model")})

    # per (tid, model) overall + per row lookup
    overall = {}
    rowmap = {}
    for r in rows:
        key = (r.get("test_id", ""), r.get("model", ""))
        overall[key] = _num(r.get("overall_score"))
        rowmap[key] = r

    # leaderboard aggregates
    agg = {}
    for m in models:
        ov = [overall[(t, mm)] for (t, mm) in overall if mm == m and overall[(t, mm)] is not None]
        lat = [_num(rowmap[(t, mm)].get("latency_sec")) for (t, mm) in rowmap if mm == m]
        lat = [x for x in lat if x is not None]
        agg[m] = {
            "quality": round(sum(ov) / len(ov), 2) if ov else None,
            "latency": round(sum(lat) / len(lat), 1) if lat else None,
            "n": len(ov),
        }
    order = sorted(models, key=lambda m: (agg[m]["quality"] is None, -(agg[m]["quality"] or 0)))

    test_ids, files = [], {}
    for r in rows:
        tid = r.get("test_id", "")
        if tid and tid not in files:
            test_ids.append(tid)
            files[tid] = r.get("input_file", "")

    p = [_HEAD]
    p.append("<header class='page'><h1>OCR Field Test</h1>"
             f"<p class='sub'>{len(order)} models · {len(test_ids)} documents · "
             "quality scored 0–5 (higher is better)</p></header>")

    # Leaderboard
    p.append("<section><h2>Leaderboard</h2><table class='board'>")
    p.append("<thead><tr><th>#</th><th>Model</th><th>Avg quality</th>"
             "<th>Avg latency</th><th>Docs</th></tr></thead><tbody>")
    for i, m in enumerate(order, 1):
        q = agg[m]["quality"]
        pct = int((q or 0) / 5 * 100)
        qcell = (f"<div class='bar'><div class='fill {_score_class(q)}' style='width:{pct}%'></div>"
                 f"<span class='barval'>{q:.2f}</span></div>" if q is not None else "<span class='muted'>—</span>")
        lat = f"{agg[m]['latency']:.1f}s" if agg[m]["latency"] is not None else "—"
        p.append(f"<tr><td class='rank'>{i}</td><td class='mname'>{html.escape(disp(m))}</td>"
                 f"<td>{qcell}</td><td>{lat}</td><td class='muted'>{agg[m]['n']}</td></tr>")
    p.append("</tbody></table>")
    p.append("<p class='legend'>Score colors: "
             "<span class='chip s5'>5</span><span class='chip s4'>4</span>"
             "<span class='chip s3'>3</span><span class='chip s2'>2</span>"
             "<span class='chip s1'>0–1</span> · winner per document is outlined.</p></section>")

    # Per-document comparison
    p.append("<section><h2>Document by document</h2>")
    for tid in test_ids:
        fname = files.get(tid, "")
        case = next((r.get("case", "") for r in rows if r.get("test_id") == tid), "")
        best = max((overall[(tid, m)] for m in models if overall.get((tid, m)) is not None),
                   default=None)

        p.append("<article class='doc'>")
        p.append(f"<div class='dhead'><span class='tid'>{html.escape(tid)}</span>"
                 f"<span class='case'>{html.escape(case)}</span>"
                 f"<span class='fn'>{html.escape(fname)}</span></div>")
        p.append("<div class='scroll'><div class='grid'>")

        src_path = _find_input(fname, input_dir) if fname else None
        uri = _img_data_uri(src_path) if src_path else None
        img = (f"<img src='{uri}' alt='{html.escape(fname)}'>" if uri
               else "<div class='noimg'>preview unavailable</div>")
        p.append(f"<div class='cell src'><div class='chead'><span class='lbl'>Source</span></div>"
                 f"<div class='imgwrap'>{img}</div></div>")

        for m in order:
            ov = overall.get((tid, m))
            note = (rowmap.get((tid, m), {}) or {}).get("notes", "")
            win = " win" if (ov is not None and best is not None and ov == best) else ""
            badge = (f"<span class='score {_score_class(ov)}'>{ov:.1f}</span>" if ov is not None
                     else "<span class='score s-na'>—</span>")
            tag = "<span class='best'>best</span>" if win else ""
            out = html.escape(_read_output(tid, m))
            note_html = f"<div class='note'>{html.escape(note)}</div>" if note else ""
            p.append(f"<div class='cell{win}'><div class='chead'>"
                     f"<span class='lbl'>{html.escape(disp(m))}{tag}</span>{badge}</div>"
                     f"{note_html}<pre class='out'>{out}</pre></div>")
        p.append("</div></div></article>")
    p.append("</section>")

    p.append("<footer class='foot'>Generated by build_viewer.py · scores are an "
             "AI-assisted first pass (review/adjust in results/metrics.csv)</footer>")
    p.append("</body></html>")
    return "\n".join(p)


_HEAD = """<!doctype html><html lang='en'><head><meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>OCR Field Test — Comparison</title>
<style>
  :root{ --line:#e5e7eb; --ink:#1f2937; --muted:#6b7280; --bg:#f6f7f9; --card:#fff; }
  *{box-sizing:border-box}
  body{font:14px/1.55 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
       margin:0;padding:32px 28px 60px;background:var(--bg);color:var(--ink)}
  .page{max-width:1280px;margin:0 auto 8px}
  h1{margin:0;font-size:24px;letter-spacing:-.01em}
  .sub{color:var(--muted);margin:4px 0 0}
  section{max-width:1280px;margin:0 auto}
  h2{font-size:15px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
     margin:34px 0 12px;font-weight:600}
  /* leaderboard */
  table.board{width:100%;border-collapse:collapse;background:var(--card);
              border:1px solid var(--line);border-radius:12px;overflow:hidden}
  .board th{font-size:11px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);
            text-align:left;padding:11px 14px;border-bottom:1px solid var(--line);font-weight:600}
  .board td{padding:12px 14px;border-bottom:1px solid var(--line);vertical-align:middle}
  .board tr:last-child td{border-bottom:0}
  .board tr:first-child .mname{font-weight:600}
  .rank{color:var(--muted);width:32px}
  .mname{white-space:nowrap}
  .bar{position:relative;background:#eef0f3;border-radius:6px;height:22px;min-width:170px;overflow:hidden}
  .fill{position:absolute;left:0;top:0;bottom:0;border-radius:6px}
  .barval{position:absolute;right:8px;top:0;line-height:22px;font-size:12px;font-weight:600}
  .legend{color:var(--muted);font-size:12px;margin:10px 2px 0}
  .chip{display:inline-block;width:20px;text-align:center;border-radius:4px;color:#fff;
        font-size:11px;font-weight:600;margin:0 1px;padding:1px 0}
  /* documents */
  .doc{background:var(--card);border:1px solid var(--line);border-radius:12px;
       padding:14px 16px;margin-bottom:16px}
  .dhead{display:flex;align-items:baseline;gap:10px;margin-bottom:12px;flex-wrap:wrap}
  .tid{font-weight:700;font-size:15px}
  .case{color:var(--ink)}
  .fn{color:var(--muted);font-size:12px;font-family:ui-monospace,Menlo,Consolas,monospace}
  .scroll{overflow-x:auto}
  .grid{display:grid;grid-auto-flow:column;grid-auto-columns:minmax(290px,1fr);gap:12px}
  .grid .src{grid-column:1;position:sticky;left:0}
  .cell{background:#fcfcfd;border:1px solid var(--line);border-radius:9px;padding:10px;min-width:290px}
  .cell.win{border-color:#16a34a;box-shadow:0 0 0 1px #16a34a inset}
  .cell.src{background:#fff}
  .chead{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}
  .lbl{font-size:12px;font-weight:600}
  .best{margin-left:6px;font-size:10px;text-transform:uppercase;letter-spacing:.04em;
        color:#16a34a;border:1px solid #16a34a;border-radius:4px;padding:0 4px}
  .score{font-size:12px;font-weight:700;color:#fff;border-radius:5px;padding:1px 7px;min-width:26px;text-align:center}
  .note{font-size:12px;color:var(--muted);margin-bottom:8px}
  pre.out{margin:0;background:#fff;border:1px solid var(--line);border-radius:7px;padding:9px;
          white-space:pre-wrap;word-break:break-word;max-height:360px;overflow:auto;
          font:12px/1.45 ui-monospace,Menlo,Consolas,monospace}
  .imgwrap{display:flex;justify-content:center}
  img{max-width:100%;max-height:440px;border:1px solid var(--line);border-radius:6px;background:#fff}
  .noimg{color:var(--muted);font-size:12px;padding:24px;text-align:center}
  .muted{color:var(--muted)}
  .s5{background:#16a34a}.s4{background:#65a30d}.s3{background:#ca8a04}
  .s2{background:#ea580c}.s1{background:#dc2626}.s-na{background:#9ca3af}
  .foot{max-width:1280px;margin:30px auto 0;color:var(--muted);font-size:12px;
        border-top:1px solid var(--line);padding-top:14px}
</style></head><body>"""


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Build a static HTML comparison viewer.")
    p.add_argument("--metrics", default="results/metrics.csv")
    p.add_argument("--input-dir", default="inputs")
    p.add_argument("--output", default="results/viewer.html")
    p.add_argument("--open", action="store_true", help="Open the file afterwards.")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    html_str = build_html(args.metrics, args.input_dir)
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        fh.write(html_str)
    abspath = os.path.abspath(args.output)
    print(f"Wrote {abspath}")
    if args.open:
        import webbrowser
        webbrowser.open("file:///" + abspath.replace(os.sep, "/"))


if __name__ == "__main__":
    main()
