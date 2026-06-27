"""Shared image/PDF helpers used by multiple runners.

PDF pages are rendered to images with PyMuPDF (no system dependency, works well
on Windows). If PyMuPDF isn't installed, we fall back to pdf2image (which needs
the Poppler binary on PATH). Either way the caller just gets PIL Images.
"""

from __future__ import annotations

import os
from typing import List

IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
PDF_EXTS = {".pdf"}
SUPPORTED_EXTS = IMAGE_EXTS | PDF_EXTS


def is_supported(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in SUPPORTED_EXTS


def is_pdf(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in PDF_EXTS


def render_pdf_to_images(path: str, dpi: int = 200) -> List["Image.Image"]:  # noqa: F821
    """Render every page of a PDF to a list of PIL Images."""
    # Preferred: PyMuPDF (import name is "fitz").
    try:
        import fitz  # type: ignore
        from PIL import Image

        images: List[Image.Image] = []
        zoom = dpi / 72.0  # 72 dpi is PDF's native unit
        matrix = fitz.Matrix(zoom, zoom)
        with fitz.open(path) as doc:
            for page in doc:
                pix = page.get_pixmap(matrix=matrix)
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                images.append(img)
        return images
    except ImportError:
        pass

    # Fallback: pdf2image (requires Poppler installed on the system PATH).
    try:
        from pdf2image import convert_from_path

        return convert_from_path(path, dpi=dpi)
    except ImportError as exc:
        raise ImportError(
            "No PDF renderer available. Install PyMuPDF (`pip install PyMuPDF`) "
            "or pdf2image + Poppler."
        ) from exc


def load_images(input_path: str, dpi: int = 200) -> List["Image.Image"]:  # noqa: F821
    """Return a list of PIL Images for any supported input.

    Single image -> one-element list. PDF -> one image per page.
    """
    from PIL import Image

    ext = os.path.splitext(input_path)[1].lower()
    if ext in IMAGE_EXTS:
        return [Image.open(input_path).convert("RGB")]
    if ext in PDF_EXTS:
        return render_pdf_to_images(input_path, dpi=dpi)
    raise ValueError(f"Unsupported file type: {ext}")
