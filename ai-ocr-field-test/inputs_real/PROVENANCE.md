# inputs_real provenance

Real public-dataset documents (safe to send to APIs; no private data).

| File | Source |
| --- | --- |
| `T1_receipt.jpg` | SROIE receipt (real, as-is) |
| `T2_receipt_blurred.jpg` | SROIE receipt (real) + Gaussian blur |
| `T3_receipt_rotated.jpg` | SROIE receipt (real) + 13deg rotation |
| `T4_receipt_lowcontrast.jpg` | SROIE receipt (real) + contrast 0.4 |
| `T5_receipt_itemized.jpg` | SROIE receipt (real, line items, as-is) |
| `T6_long_doc.pdf` | arXiv:1706.03762 (real 15-page PDF) |
| `T7_form.png` | FUNSD form (real scan, mixed layout) |
| `T8_form_handwritten.png` | FUNSD form (real scan w/ handwriting) |
| `T9_wrong_total_invoice.pdf` | synthetic (kept: must be fabricated / not sourced) |
| `T10_multilingual_doc.pdf` | synthetic (kept: must be fabricated / not sourced) |

**Sources / licenses (attribute before publishing the images):**
- SROIE (ICDAR 2019) — scanned receipts, research use.
- FUNSD — scanned forms, research-only license.
- arXiv:1706.03762 — paper PDF (author copyright; used only as an OCR input).
- T9/T10 — synthetic (generated locally).
