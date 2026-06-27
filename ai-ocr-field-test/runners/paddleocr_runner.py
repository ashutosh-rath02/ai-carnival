"""PaddleOCR runner — open-source OCR baseline.

Runs PaddleOCR locally. Images are OCR'd directly; PDFs are rendered to one image
per page first. All pages are saved to a single text file with page separators:

    --- PAGE 1 ---
    text here

    --- PAGE 2 ---
    text here

PaddleOCR/paddlepaddle can be heavy to install (especially on Windows). The
import is lazy and the base runner converts any failure into a clean
``status='failed'`` result, so the rest of the experiment still runs without it.
"""

from __future__ import annotations

import os

# paddlepaddle 3.x's oneDNN (MKL-DNN) CPU backend crashes on some Windows builds
# with: "ConvertPirAttribute2RuntimeAttribute not support ...onednn_instruction".
# Disabling oneDNN before paddle is imported forces stable native CPU kernels.
# Set PADDLE_ENABLE_MKLDNN=1 to re-enable it if your build is unaffected.
if os.environ.get("PADDLE_ENABLE_MKLDNN", "0") not in ("1", "true", "True"):
    os.environ.setdefault("FLAGS_use_mkldnn", "0")

from .base import BaseRunner, test_id_from_path
from .pdf_utils import load_images

# Lightweight PP-OCRv5 mobile models: small, fast to download, and quick on CPU.
# Override with PADDLE_DET_MODEL / PADDLE_REC_MODEL (e.g. PP-OCRv5_server_rec for
# higher accuracy at the cost of speed and a much larger download).
DEFAULT_DET_MODEL = "PP-OCRv5_mobile_det"
DEFAULT_REC_MODEL = "PP-OCRv5_mobile_rec"


class PaddleOCRRunner(BaseRunner):
    name = "paddleocr"
    output_subdir = "paddleocr"

    def __init__(self, lang: str = "en"):
        self.lang = lang
        self.det_model = (os.getenv("PADDLE_DET_MODEL") or DEFAULT_DET_MODEL).strip()
        self.rec_model = (os.getenv("PADDLE_REC_MODEL") or DEFAULT_REC_MODEL).strip()
        self.enable_mkldnn = os.environ.get("PADDLE_ENABLE_MKLDNN", "0") in (
            "1", "true", "True"
        )
        self._ocr = None  # built lazily on first use

    def _get_ocr(self):
        """Instantiate (and cache) a PaddleOCR engine, tolerating API changes."""
        if self._ocr is not None:
            return self._ocr
        from paddleocr import PaddleOCR

        # Kwarg names changed across PaddleOCR 2.x -> 3.x; try newest-friendly
        # combos and degrade gracefully.
        #
        # On 3.x the default pipeline also runs doc-orientation + doc-unwarping
        # (UVDoc) models, which are large and slow on CPU. We turn those off for a
        # practical raw-text baseline but keep textline orientation (small, and it
        # helps the rotated/oriented test cases). We also pin the lightweight
        # mobile det/rec models and disable oneDNN to avoid the CPU crash above.
        for kwargs in (
            {
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": True,
                "text_detection_model_name": self.det_model,
                "text_recognition_model_name": self.rec_model,
                "enable_mkldnn": self.enable_mkldnn,
            },
            {
                "use_doc_orientation_classify": False,
                "use_doc_unwarping": False,
                "use_textline_orientation": True,
                "lang": self.lang,
            },
            {"use_angle_cls": True, "lang": self.lang, "show_log": False},
            {"use_textline_orientation": True, "lang": self.lang},
            {"lang": self.lang},
        ):
            try:
                self._ocr = PaddleOCR(**kwargs)
                return self._ocr
            except (TypeError, ValueError):
                continue
        # Last resort: defaults only.
        self._ocr = PaddleOCR()
        return self._ocr

    def _ocr_image(self, image) -> str:
        """Run OCR on one PIL image and return newline-joined text."""
        import numpy as np

        ocr = self._get_ocr()
        arr = np.array(image)

        result = None
        for call in (
            lambda: ocr.ocr(arr, cls=True),
            lambda: ocr.ocr(arr),
            lambda: ocr.predict(arr),
        ):
            try:
                result = call()
                break
            except (TypeError, AttributeError):
                continue

        lines: list[str] = []
        _harvest_text(result, lines)
        return "\n".join(lines)

    def extract(self, input_path: str, output_dir: str) -> str:
        test_id = test_id_from_path(input_path)
        out_path = os.path.join(output_dir, f"{test_id}_output.txt")

        images = load_images(input_path)
        sections = []
        for page_num, image in enumerate(images, start=1):
            text = self._ocr_image(image)
            sections.append(f"--- PAGE {page_num} ---\n{text}")

        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write("\n\n".join(sections) + "\n")
        return out_path


def _harvest_text(node, out: list) -> None:
    """Recursively pull recognized text out of PaddleOCR results.

    Works across PaddleOCR versions because it looks for the two shapes that
    actually carry text, regardless of nesting:
      - a ``(text: str, confidence: number)`` pair (classic 2.x lines), and
      - a dict with a ``rec_texts`` list (3.x predict output).
    Bounding-box coordinates are lists of numbers and are simply ignored.
    """
    if node is None:
        return
    if isinstance(node, dict):
        if "rec_texts" in node and isinstance(node["rec_texts"], (list, tuple)):
            out.extend(str(t) for t in node["rec_texts"])
            return
        for value in node.values():
            _harvest_text(value, out)
        return
    if isinstance(node, (list, tuple)):
        if (
            len(node) == 2
            and isinstance(node[0], str)
            and isinstance(node[1], (int, float))
        ):
            out.append(node[0])
            return
        for item in node:
            _harvest_text(item, out)
