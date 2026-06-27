# AI OCR Field Test

A lightweight experiment harness to compare OCR / document-AI tools on **messy
real-world documents** — not clean demo PDFs. Point it at a folder of documents,
run one or more extractors, save raw outputs + latency, score the results by
hand, and generate a Markdown comparison report.

> The goal isn't a SaaS product. It's a one-week practical benchmark that
> produces publishable results: a repo, a comparison table, screenshots, and a
> short write-up.

## Why this exists

I tested OCR/document AI tools on messy real-world documents to see what actually
works beyond clean demos. Clean PDFs are basically solved. Messy business docs —
blurry photos, rotated scans, dense tables, handwriting, multilingual pages — are
where tools diverge.

## What I tested

- **PaddleOCR** — open-source OCR baseline, runs locally on CPU (raw text).
- **VLM** — a vision LLM (Gemini by default via `gemini-flash-latest`, OpenAI
  optional) that extracts *structured fields* and reasons about the document.
- **Mistral OCR** — managed OCR API, returns clean Markdown (incl. tables).
- **Unlimited-OCR** — Baidu's open-source long-document OCR. GPU-only, so it runs
  via its OpenAI-compatible server (see `colab/unlimited_ocr_colab.ipynb`); the
  runner just points at that endpoint. Fails gracefully when no endpoint is set.

## Test cases

The harness processes whatever valid files exist in `inputs/` — you don't need
all 10. Supported formats: `.pdf`, `.png`, `.jpg`, `.jpeg`.

| ID  | Case                              | What it tests          |
| --- | --------------------------------- | ---------------------- |
| T1  | Clean digital invoice             | Easy baseline          |
| T2  | Blurry invoice photo              | OCR robustness         |
| T3  | Rotated invoice                   | Orientation handling   |
| T4  | Low-contrast scan                 | Image quality          |
| T5  | Table-heavy invoice/packing list  | Table structure        |
| T6  | Long 10-page PDF                  | Long document handling |
| T7  | Mixed text + image PDF            | Layout understanding   |
| T8  | Handwritten field on printed form | Handwriting weakness   |
| T9  | Invoice with wrong total          | Reasoning/validation   |
| T10 | Multilingual document             | Multilingual OCR       |

The `test_id` is parsed from the leading `T<n>` in each filename.

## Scoring (0–5)

Scores are filled in **manually** in `results/metrics.csv` after you read each
model's output:

```text
0 = failed / unusable
1 = mostly wrong
2 = partial extraction
3 = usable with human review
4 = mostly correct
5 = production-ready
```

Dimensions: `text_score`, `field_score`, `table_score`, `hallucination_score`
(higher = hallucinated less). `overall_score = average of the four`.

## How to run

```bash
python -m venv venv
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # then add your API keys
```

> On Windows you can call the venv Python directly without activating, e.g.
> `venv\Scripts\python scripts\run_experiment.py ...`

Add your own documents to `inputs/` — or generate synthetic stand-ins to try the
whole pipeline first:

```bash
# (optional) create synthetic T1–T10 stand-in documents
python scripts/make_synthetic_inputs.py

# Run any subset of models
python scripts/run_experiment.py --models paddleocr
python scripts/run_experiment.py --models paddleocr vlm
python scripts/run_experiment.py --models paddleocr vlm mistral_ocr unlimited_ocr

# Build the scoring sheet, score it (or use the viewer), then generate the report
python scripts/init_metrics.py
python scripts/build_viewer.py --open      # eyeball source vs each model's output
python scripts/generate_report.py
```

Useful flags: `--input-dir`, `--output-dir`, `--metrics`, `--limit N`.

To include **Unlimited-OCR**, run `colab/unlimited_ocr_colab.ipynb` on a GPU,
paste the printed `UNLIMITED_OCR_BASE_URL=...` into `.env`, then add
`unlimited_ocr` to `--models`.

## Folder structure

```text
ai-ocr-field-test/
  inputs/            # your test documents (you add these)
  outputs/
    paddleocr/       # raw .txt per document
    vlm/             # structured .json per document
    mistral_ocr/     # .md per document
    unlimited_ocr/   # .md per document (GPU endpoint)
  results/
    run_log.csv      # auto: timestamp/latency/status per run (gitignored)
    metrics.csv      # scoring sheet (you fill the score columns)
    insights.md      # qualitative verdicts (merged into the report)
    final_report.md  # generated comparison report
    viewer.html      # generated side-by-side viewer
  scripts/           # run_experiment / init_metrics / generate_report /
                     #   build_viewer / make_synthetic_inputs
  runners/           # base + paddleocr / vlm / mistral_ocr / unlimited_ocr
  evaluators/        # scoring template + helpers
  prompts/           # vlm_extraction_prompt.txt
  colab/             # unlimited_ocr_colab.ipynb (GPU server)
  post/              # linkedin_draft.md, carousel_outline.md
  screenshots/       # captures for the write-up
```

## Results

Generated results live in `results/final_report.md` (winners per test case,
average score per model, best overall, plus the qualitative verdicts from
`results/insights.md`). Use `results/viewer.html` to compare outputs visually.

**4 models × 10 real documents** (SROIE receipts, FUNSD forms, an arXiv PDF, plus
2 synthetic edge cases). Scores are an AI-assisted first pass (0–5):

| Model | Avg quality /5 | Avg latency | Notes |
| --- | --- | --- | --- |
| Gemini 3.5 Flash (VLM) | **4.72** | 16.0s | Best overall; refused 1 doc → GPT-5.5 fallback |
| Mistral OCR | 4.60 | **4.2s** | Most reliable all-rounder; clean tables |
| Unlimited-OCR | 3.90 | 40.3s | Free/open, layout + HTML tables — hallucinated on blur |
| PaddleOCR | 2.83 | 150s | Free/local CPU baseline; weakest on messy docs |

### Each model fails differently
- **PaddleOCR** → **blanked** on the blurry receipt (near-empty output).
- **Unlimited-OCR** → **hallucinated** on the blurry receipt (invented text + leaked
  its own internal prompt rules).
- **Gemini 3.5 Flash** → **refused** a FUNSD form (`finish_reason 4: reciting from
  copyrighted material` — it recognized the public dataset) → fell back to
  **GPT-5.5**; it also *summarizes* the 15-page paper instead of OCR-ing the text.
- **Mistral** → read everything cleanly.

> Models tested at latest: **Gemini 3.5 Flash** (VLM) with **GPT-5.5** fallback,
> **mistral-ocr-latest**, **Unlimited-OCR**, **PP-OCRv5**. Scores are a first-pass
> AI-assisted estimate (no ground truth) — review in `results/metrics.csv`. Sample
> documents are public datasets — see `inputs_real/PROVENANCE.md` for sources/licenses.

## Installation notes (read if something fails)

- **PaddleOCR / paddlepaddle on Windows** can be the trickiest install. If
  `pip install -r requirements.txt` fails on Paddle, install the rest first, then
  install Paddle separately following the official guide. The repo is designed to
  still run with **VLM-only** if Paddle isn't available — the PaddleOCR runner
  imports lazily and reports a clean `failed` status instead of crashing.
- **PDF rendering** uses **PyMuPDF** (`pip install PyMuPDF`), which needs no
  system binaries. `pdf2image` is an optional fallback and would require the
  Poppler system binary on your PATH — you can ignore it if PyMuPDF is installed.
- **API keys** go in `.env`. Missing keys never crash a run; the runner returns
  `status=failed` with a clear error so the rest of the experiment continues.
- **Mistral SDK:** pinned to `mistralai==1.12.4`. The 2.x wheels ship without the
  top-level `Mistral` export on Windows, breaking `from mistralai import Mistral`.
- **PaddleOCR on Windows:** paddle 3.x's oneDNN CPU backend can crash
  (`ConvertPirAttribute2RuntimeAttribute`). The runner disables oneDNN and uses
  the lightweight PP-OCRv5 mobile models; set `PADDLE_ENABLE_MKLDNN=1` /
  `PADDLE_DET_MODEL` / `PADDLE_REC_MODEL` to change this.
- **Unlimited-OCR is GPU-only** (CUDA). It can't run on a CPU machine — use the
  Colab notebook (or any cloud GPU) and point `UNLIMITED_OCR_BASE_URL` at it.

## Final verdict

Clean documents are solved — every model handled the clean and low-contrast
receipts. **Messy inputs separate the field, and each model fails differently:**
Gemini (4.65/5, best overall) reasons and catches a wrong total, but *refuses*
documents it recognizes from training data and degrades on long full-text;
Unlimited-OCR (3.90/5, free/open, great layout + HTML tables) can *hallucinate* on
blur; PaddleOCR (2.83/5) *blanks* on blur and is slow on CPU. **Mistral OCR
(4.60/5, ~4 s/doc) was the most reliable all-rounder** — no refusals, no
hallucinations, clean tables everywhere. The practical recommendation is **fast,
robust OCR (Mistral or self-hosted Unlimited-OCR) for extraction + a VLM for
fields/validation**, with a fallback VLM provider for when one refuses a document.
(Run on real public documents; scores are a first-pass AI-assisted estimate.)

## Content output

Draft public content lives in `post/`:
- `post/linkedin_draft.md`
- `post/carousel_outline.md`
