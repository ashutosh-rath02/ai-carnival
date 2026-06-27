"""Mistral OCR runner — optional trending OCR API.

Saves output to ``outputs/mistral_ocr/{test_id}_output.md``.

Behavior required by the PRD:
  - If ``MISTRAL_API_KEY`` is missing, do not crash: fail cleanly with the message
    ``MISTRAL_API_KEY not configured``.
  - The repo must still work with PaddleOCR + VLM only.

This implements a best-effort call against the Mistral OCR endpoint via the
``mistralai`` SDK. The exact request/response shape may drift between SDK
versions, so response parsing is defensive and there are TODO markers where you
may need to adjust to the current API docs.
"""

from __future__ import annotations

import base64
import os

from .base import BaseRunner, test_id_from_path
from .pdf_utils import is_pdf

DEFAULT_MODEL = "mistral-ocr-latest"


class MistralOCRRunner(BaseRunner):
    name = "mistral_ocr"
    output_subdir = "mistral_ocr"

    def __init__(self):
        _load_dotenv()
        self.api_key = (os.getenv("MISTRAL_API_KEY") or "").strip()
        self.model = (os.getenv("MISTRAL_OCR_MODEL") or DEFAULT_MODEL).strip()

    def extract(self, input_path: str, output_dir: str) -> str:
        if not self.api_key:
            # Exact message required by the PRD.
            raise RuntimeError("MISTRAL_API_KEY not configured")

        try:
            from mistralai import Mistral
        except ImportError as exc:
            raise ImportError(
                "mistralai SDK not installed. Run `pip install mistralai` to use "
                "the Mistral OCR runner."
            ) from exc

        client = Mistral(api_key=self.api_key)

        # Build the document payload as a base64 data URL (works for local files
        # without a separate upload step).
        # TODO: if the API changes, you may prefer client.files.upload() + a
        # signed URL for large PDFs. See https://docs.mistral.ai/ for current docs.
        document = _build_document_payload(input_path)

        response = client.ocr.process(model=self.model, document=document)

        markdown = _response_to_markdown(response)

        test_id = test_id_from_path(input_path)
        out_path = os.path.join(output_dir, f"{test_id}_output.md")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        return out_path


def _build_document_payload(input_path: str) -> dict:
    data = _file_to_data_url(input_path)
    if is_pdf(input_path):
        return {"type": "document_url", "document_url": data}
    return {"type": "image_url", "image_url": data}


def _file_to_data_url(input_path: str) -> str:
    ext = os.path.splitext(input_path)[1].lower()
    mime = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(ext, "application/octet-stream")
    with open(input_path, "rb") as fh:
        encoded = base64.b64encode(fh.read()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _response_to_markdown(response) -> str:
    """Pull per-page markdown out of the OCR response, defensively.

    Handles both pydantic-style objects (``response.pages[i].markdown``) and
    plain dicts. Falls back to the stringified response so output is never empty.
    """
    pages = getattr(response, "pages", None)
    if pages is None and isinstance(response, dict):
        pages = response.get("pages")

    if not pages:
        return str(response)

    parts = []
    for idx, page in enumerate(pages, start=1):
        md = getattr(page, "markdown", None)
        if md is None and isinstance(page, dict):
            md = page.get("markdown")
        parts.append(f"<!-- PAGE {idx} -->\n{md or ''}")
    return "\n\n".join(parts) + "\n"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
