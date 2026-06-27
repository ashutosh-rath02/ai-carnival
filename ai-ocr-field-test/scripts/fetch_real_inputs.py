"""Fetch REAL public test documents into inputs_real/ (non-destructive).

Pulls genuinely real documents from public research datasets so you can run the
benchmark on real-world data instead of the synthetic stand-ins. These are public,
anonymized datasets — safe to send to the cloud OCR/VLM APIs.

Sources (attribute these if you publish the document images):
  - SROIE (ICDAR 2019) scanned receipts  -> T1-T5
  - arXiv:1706.03762 (real 15-page PDF)   -> T6
  - FUNSD scanned forms (printed + handwritten) -> T7, T8
  - T9 (wrong total) / T10 (multilingual) stay synthetic — copied from inputs/.

T2/T3/T4 apply a controlled blur / rotation / low-contrast to a real receipt so
each "image quality" case is genuinely exercised on real document content.

Usage:
    python scripts/fetch_real_inputs.py
    python scripts/run_experiment.py --models paddleocr vlm mistral_ocr --input-dir inputs_real
"""

from __future__ import annotations

import io
import os
import shutil
import zipfile

import requests
from PIL import Image, ImageEnhance, ImageFilter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(REPO, "inputs_real")

SROIE_API = "https://api.github.com/repos/zzzDavid/ICDAR-2019-SROIE/contents/data/img"
ARXIV_PDF = "https://arxiv.org/pdf/1706.03762"
FUNSD_ZIP = "https://guillaumejaume.github.io/FUNSD/dataset.zip"


def _save_jpg(img, name, q=90):
    img.convert("RGB").save(os.path.join(DST, name), quality=q)


def fetch_sroie(prov):
    items = requests.get(SROIE_API, timeout=60).json()
    imgs = [it for it in items if it["name"].lower().endswith((".jpg", ".jpeg", ".png"))]

    def grab(i):
        return Image.open(io.BytesIO(requests.get(imgs[i]["download_url"], timeout=60).content))

    _save_jpg(grab(0), "T1_receipt.jpg")
    _save_jpg(grab(1).filter(ImageFilter.GaussianBlur(2.2)), "T2_receipt_blurred.jpg", 75)
    _save_jpg(grab(2).rotate(13, expand=True, fillcolor="white"), "T3_receipt_rotated.jpg", 88)
    _save_jpg(ImageEnhance.Contrast(grab(3).convert("RGB")).enhance(0.4), "T4_receipt_lowcontrast.jpg", 80)
    _save_jpg(grab(4), "T5_receipt_itemized.jpg")
    prov += [
        ("T1_receipt.jpg", "SROIE receipt (real, as-is)"),
        ("T2_receipt_blurred.jpg", "SROIE receipt (real) + Gaussian blur"),
        ("T3_receipt_rotated.jpg", "SROIE receipt (real) + 13deg rotation"),
        ("T4_receipt_lowcontrast.jpg", "SROIE receipt (real) + low contrast"),
        ("T5_receipt_itemized.jpg", "SROIE receipt (real, line items, as-is)"),
    ]


def fetch_arxiv(prov):
    pdf = requests.get(ARXIV_PDF, timeout=120).content
    open(os.path.join(DST, "T6_long_doc.pdf"), "wb").write(pdf)
    prov.append(("T6_long_doc.pdf", "arXiv:1706.03762 (real 15-page PDF)"))


def fetch_funsd(prov):
    zf = zipfile.ZipFile(io.BytesIO(requests.get(FUNSD_ZIP, timeout=180).content))
    # Real form images live under dataset/testing_data/images/*.png. Exclude the
    # macOS __MACOSX/._* metadata stubs (which are tiny and not valid images).
    real = sorted(
        (i.file_size, i.filename)
        for i in zf.infolist()
        if i.filename.lower().endswith(".png")
        and "testing_data/images/" in i.filename
        and "__MACOSX" not in i.filename
    )
    real.sort(reverse=True)
    for slot, (_sz, fn) in zip(["T7_form.png", "T8_form_handwritten.png"], real[:2]):
        open(os.path.join(DST, slot), "wb").write(zf.read(fn))
    prov += [
        ("T7_form.png", "FUNSD form (real scan, mixed layout)"),
        ("T8_form_handwritten.png", "FUNSD form (real scan w/ handwriting)"),
    ]


def keep_synthetic(prov):
    for name in ("T9_wrong_total_invoice.pdf", "T10_multilingual_doc.pdf"):
        src = os.path.join(REPO, "inputs", name)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(DST, name))
            prov.append((name, "synthetic (kept: fabricated / not publicly sourced)"))


def write_provenance(prov):
    with open(os.path.join(DST, "PROVENANCE.md"), "w", encoding="utf-8") as fh:
        fh.write("# inputs_real provenance\n\nReal public-dataset documents "
                 "(safe to send to APIs; no private data).\n\n| File | Source |\n| --- | --- |\n")
        for name, src in prov:
            fh.write(f"| `{name}` | {src} |\n")
        fh.write("\n**Licenses (attribute before publishing the images):** SROIE "
                 "(ICDAR 2019, research use); FUNSD (research-only); arXiv:1706.03762 "
                 "(paper PDF, used only as an OCR input); T9/T10 synthetic.\n")


def main():
    os.makedirs(DST, exist_ok=True)
    prov: list[tuple[str, str]] = []
    for name, fn in [("SROIE", fetch_sroie), ("arXiv", fetch_arxiv), ("FUNSD", fetch_funsd)]:
        try:
            fn(prov)
            print(f"{name}: ok")
        except Exception as exc:  # noqa: BLE001
            print(f"{name} FAILED: {type(exc).__name__}: {str(exc)[:150]}")
    keep_synthetic(prov)
    write_provenance(prov)
    print(f"\nWrote {len(prov)} docs to {DST}")
    print("Run: python scripts/run_experiment.py --models paddleocr vlm mistral_ocr "
          "--input-dir inputs_real")


if __name__ == "__main__":
    main()
