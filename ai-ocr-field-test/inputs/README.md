# Inputs

Drop your test documents here. The harness processes **whatever valid files are present** —
it does not require all 10. Supported formats: `.pdf`, `.png`, `.jpg`, `.jpeg`.

The `test_id` is taken from the leading `T<number>` in the filename (e.g. `T3_rotated_invoice.jpg`
→ `T3`). If a filename has no `T<n>` prefix, the full stem is used as the id.

## Suggested test set

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

## Expected filenames

```text
T1_clean_invoice.pdf
T2_blurry_invoice.jpg
T3_rotated_invoice.jpg
T4_low_contrast_scan.jpg
T5_table_invoice.pdf
T6_long_10_page.pdf
T7_mixed_layout.pdf
T8_handwritten_form.jpg
T9_wrong_total_invoice.pdf
T10_multilingual_doc.pdf
```
