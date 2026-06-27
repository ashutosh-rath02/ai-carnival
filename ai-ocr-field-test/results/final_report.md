# AI OCR Field Test: 3 OCR/Document AI Tools on 10 Messy Documents

_Generated 2026-06-26._

## Experiment summary

A practical field test comparing OCR / document-AI tools on messy real-world documents. Each model ran over the same set of documents; raw outputs were scored by hand on a 0-5 scale across four dimensions.

## Models tested

- `mistral_ocr`
- `paddleocr`
- `unlimited_ocr`
- `vlm`

## Test cases

| ID | Case | Input file |
| --- | --- | --- |
| T1 | Clean digital invoice | T1_receipt.jpg |
| T2 | Blurry invoice photo | T2_receipt_blurred.jpg |
| T3 | Rotated invoice | T3_receipt_rotated.jpg |
| T4 | Low-contrast scan | T4_receipt_lowcontrast.jpg |
| T5 | Table-heavy invoice/packing list | T5_receipt_itemized.jpg |
| T6 | Long 10-page PDF | T6_long_doc.pdf |
| T7 | Mixed text + image PDF | T7_form.png |
| T8 | Handwritten field on printed form | T8_form_handwritten.png |
| T9 | Invoice with wrong total | T9_wrong_total_invoice.pdf |
| T10 | Multilingual document | T10_multilingual_doc.pdf |

## Scoring method

Each output was scored 0-5 per dimension:

- **0** = failed / unusable
- **1** = mostly wrong
- **2** = partial extraction
- **3** = usable with human review
- **4** = mostly correct
- **5** = production-ready

Dimensions: text, field, table, hallucination (higher = hallucinated less). **Overall = average of the four.**

## Results

| Test | Model | Text | Field | Table | Halluc. | Latency (s) | Overall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T1 | paddleocr | 3.00 | 2.00 | 2.00 | 4.00 | 17.57 | 2.75 |
| T1 | vlm | 5.00 | 5.00 | 4.00 | 5.00 | 10.13 | 4.75 |
| T1 | mistral_ocr | 4.00 | 4.00 | 4.00 | 5.00 | 4.92 | 4.25 |
| T1 | unlimited_ocr | 4.00 | 4.00 | 5.00 | 4.00 | 27.68 | 4.25 |
| T2 | paddleocr | 1.00 | 1.00 | 1.00 | 3.00 | 1.74 | 1.50 |
| T2 | vlm | 5.00 | 5.00 | 5.00 | 5.00 | 15.07 | 5.00 |
| T2 | mistral_ocr | 5.00 | 5.00 | 5.00 | 5.00 | 3.95 | 5.00 |
| T2 | unlimited_ocr | 1.00 | 1.00 | 1.00 | 1.00 | 41.30 | 1.00 |
| T3 | paddleocr | 3.00 | 2.00 | 2.00 | 4.00 | 20.80 | 2.75 |
| T3 | vlm | 5.00 | 5.00 | 5.00 | 5.00 | 19.95 | 5.00 |
| T3 | mistral_ocr | 4.00 | 4.00 | 4.00 | 5.00 | 3.70 | 4.25 |
| T3 | unlimited_ocr | 4.00 | 4.00 | 4.00 | 4.00 | 27.57 | 4.00 |
| T4 | paddleocr | 3.00 | 2.00 | 2.00 | 4.00 | 23.76 | 2.75 |
| T4 | vlm | 5.00 | 5.00 | 4.00 | 5.00 | 11.98 | 4.75 |
| T4 | mistral_ocr | 4.00 | 4.00 | 4.00 | 5.00 | 4.42 | 4.25 |
| T4 | unlimited_ocr | 5.00 | 5.00 | 5.00 | 5.00 | 37.47 | 5.00 |
| T5 | paddleocr | 3.00 | 3.00 | 2.00 | 3.00 | 23.81 | 2.75 |
| T5 | vlm | 5.00 | 5.00 | 4.00 | 5.00 | 16.25 | 4.75 |
| T5 | mistral_ocr | 5.00 | 5.00 | 5.00 | 5.00 | 5.26 | 5.00 |
| T5 | unlimited_ocr | 4.00 | 4.00 | 4.00 | 4.00 | 40.33 | 4.00 |
| T6 | paddleocr | 4.00 | 3.00 | 3.00 | 4.00 | 1288.38 | 3.50 |
| T6 | vlm | 3.00 | 4.00 | 3.00 | 5.00 | 13.05 | 3.75 |
| T6 | mistral_ocr | 5.00 | 4.00 | 4.00 | 5.00 | 3.66 | 4.50 |
| T6 | unlimited_ocr | 5.00 | 4.00 | 4.00 | 5.00 | 162.25 | 4.50 |
| T7 | paddleocr | 3.00 | 2.00 | 2.00 | 4.00 | 45.32 | 2.75 |
| T7 | vlm | 5.00 | 5.00 | 4.00 | 5.00 | 37.80 | 4.75 |
| T7 | mistral_ocr | 5.00 | 4.00 | 4.00 | 5.00 | 4.76 | 4.50 |
| T7 | unlimited_ocr | 4.00 | 4.00 | 4.00 | 4.00 | 23.94 | 4.00 |
| T8 | paddleocr | 3.00 | 2.00 | 2.00 | 3.00 | 20.62 | 2.50 |
| T8 | vlm | 5.00 | 5.00 | 4.00 | 5.00 | 10.43 | 4.75 |
| T8 | mistral_ocr | 5.00 | 5.00 | 4.00 | 5.00 | 3.73 | 4.75 |
| T8 | unlimited_ocr | 4.00 | 4.00 | 3.00 | 4.00 | 18.61 | 3.75 |
| T9 | paddleocr | 5.00 | 4.00 | 2.00 | 5.00 | 23.36 | 4.00 |
| T9 | vlm | 5.00 | 5.00 | 5.00 | 5.00 | 12.39 | 5.00 |
| T9 | mistral_ocr | 5.00 | 5.00 | 5.00 | 5.00 | 2.21 | 5.00 |
| T9 | unlimited_ocr | 5.00 | 4.00 | 4.00 | 5.00 | 12.49 | 4.50 |
| T10 | paddleocr | 3.00 | 3.00 | 2.00 | 4.00 | 30.40 | 3.00 |
| T10 | vlm | 5.00 | 5.00 | 4.00 | 5.00 | 12.64 | 4.75 |
| T10 | mistral_ocr | 5.00 | 4.00 | 4.00 | 5.00 | 5.01 | 4.50 |
| T10 | unlimited_ocr | 4.00 | 4.00 | 4.00 | 4.00 | 11.05 | 4.00 |

## Winner by test case

| Test | Case | Winner | Overall |
| --- | --- | --- | --- |
| T1 | Clean digital invoice | vlm | 4.75 |
| T2 | Blurry invoice photo | mistral_ocr | 5.00 |
| T3 | Rotated invoice | vlm | 5.00 |
| T4 | Low-contrast scan | unlimited_ocr | 5.00 |
| T5 | Table-heavy invoice/packing list | mistral_ocr | 5.00 |
| T6 | Long 10-page PDF | mistral_ocr | 4.50 |
| T7 | Mixed text + image PDF | vlm | 4.75 |
| T8 | Handwritten field on printed form | mistral_ocr | 4.75 |
| T9 | Invoice with wrong total | mistral_ocr | 5.00 |
| T10 | Multilingual document | vlm | 4.75 |

## Average score by model

| Model | Avg overall | Avg latency (s) | Docs scored |
| --- | --- | --- | --- |
| mistral_ocr | 4.60 | 4.16 | 10 |
| paddleocr | 2.83 | 149.58 | 10 |
| unlimited_ocr | 3.90 | 40.27 | 10 |
| vlm | 4.72 | 15.97 | 10 |

## Best overall model

**vlm** with an average overall score of **4.72**.

## Most Surprising Result

**On the same blurry receipt, the models failed in opposite ways.** PaddleOCR
returned almost **nothing** (blanked). Unlimited-OCR **hallucinated** — it invented
unrelated text and leaked its own internal prompt rules into the output. Gemini 3.5
Flash and Mistral both read it fine. Separately, **Gemini still *refused* a FUNSD
form** (`finish_reason 4: reciting from copyrighted material`) because it recognized
the public dataset — that one was completed with GPT-5.5. Blank vs. hallucinate vs.
refuse: three distinct, production-relevant failure modes across one small real set.

> Models: Gemini 3.5 Flash (VLM, with GPT-5.5 fallback on refusal), Mistral OCR
> (`mistral-ocr-latest`), Baidu Unlimited-OCR (free GPU), PaddleOCR (PP-OCRv5).
> Data: real SROIE receipts + FUNSD forms + an arXiv PDF, plus 2 synthetic edge
> cases. Scores are an AI-assisted first pass — review/adjust in the viewer.

## Worst Failure

**Unlimited-OCR on the blurry receipt (T2)** — instead of admitting it couldn't read
the blur, it confidently hallucinated unrelated Chinese text and exposed its system
prompt. A confident wrong answer is worse than an empty one. Runner-up: **PaddleOCR
on T2** (near-empty output). Both show blur is still the great separator.

## Practical Verdict

- **Upgrading to the latest VLM helped:** Gemini 3.5 Flash read documents that older
  Gemini refused, cutting the recitation refusals from 3 docs to 1. But the filter
  is still real — a VLM can refuse documents it recognizes, so keep a fallback.
- **Failure modes differ and matter in production:** Gemini *refuses* known docs and
  degrades on long full-text (it summarizes the 15-page paper instead of OCR-ing it);
  Unlimited-OCR can *hallucinate* on degraded inputs; PaddleOCR *blanks* on blur.
- **Mistral OCR was the most reliable all-rounder** — fastest (4.2s/doc), no refusals,
  no hallucinations, clean Markdown + tables across blur, rotation, forms, and the PDF.
- **Unlimited-OCR is the standout free/open option** — layout + HTML tables + bounding
  boxes, ran the full 15-page paper on a free Kaggle T4 — but GPU-bound and can hallucinate.
- **Best setup:** Mistral (or self-hosted Unlimited-OCR) for extraction **+ a VLM for
  fields/validation**, with a **fallback VLM provider** for refusals.
