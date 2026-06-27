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
