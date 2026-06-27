"""Unlimited-OCR runner — Baidu's open-source long-document OCR model.

Unlimited-OCR (baidu/Unlimited-OCR) is a self-hosted GPU model. It cannot run on
a CPU-only machine, but it ships an OpenAI-compatible server (via SGLang), so this
runner just points the OpenAI client at that endpoint. Run the model on a GPU
(e.g. the provided Google Colab notebook), expose its port with a tunnel, and set
the resulting URL here.

Env vars:
    UNLIMITED_OCR_BASE_URL   e.g. https://xxxx.trycloudflare.com/v1   (required)
    UNLIMITED_OCR_API_KEY    any string; SGLang ignores it (default: "EMPTY")
    UNLIMITED_OCR_MODEL      served model name (default: "Unlimited-OCR")
    UNLIMITED_OCR_PROMPT     instruction (default: "document parsing.")

Output: outputs/unlimited_ocr/{test_id}_output.md
"""

from __future__ import annotations

import base64
import io
import os

from .base import BaseRunner, test_id_from_path
from .pdf_utils import load_images

DEFAULT_MODEL = "Unlimited-OCR"
DEFAULT_PROMPT = "document parsing."


class UnlimitedOCRRunner(BaseRunner):
    name = "unlimited_ocr"
    output_subdir = "unlimited_ocr"

    def __init__(self, max_pages: int = 30):
        _load_dotenv()
        self.base_url = (os.getenv("UNLIMITED_OCR_BASE_URL") or "").strip()
        self.api_key = (os.getenv("UNLIMITED_OCR_API_KEY") or "EMPTY").strip()
        self.model = (os.getenv("UNLIMITED_OCR_MODEL") or DEFAULT_MODEL).strip()
        self.prompt = (os.getenv("UNLIMITED_OCR_PROMPT") or DEFAULT_PROMPT).strip()
        self.max_pages = max_pages

    def extract(self, input_path: str, output_dir: str) -> str:
        if not self.base_url:
            raise RuntimeError(
                "UNLIMITED_OCR_BASE_URL not configured. Start the model on a GPU "
                "(see colab/unlimited_ocr_colab.ipynb) and set the tunnel URL."
            )
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("openai SDK not installed (pip install openai).") from exc

        # Fail fast on a dead/unreachable endpoint instead of hanging on the
        # client's long default timeout; multi-page docs still get a few minutes.
        client = OpenAI(
            base_url=self.base_url, api_key=self.api_key,
            timeout=180.0, max_retries=1,
        )

        # Unlimited-OCR parses many pages in one forward pass, so send all pages.
        images = load_images(input_path)[: self.max_pages]
        content = [{"type": "text", "text": self.prompt}]
        for image in images:
            content.append(
                {"type": "image_url", "image_url": {"url": _to_data_url(image)}}
            )

        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
        )
        markdown = response.choices[0].message.content or ""

        test_id = test_id_from_path(input_path)
        out_path = os.path.join(output_dir, f"{test_id}_output.md")
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(markdown)
        return out_path


def _to_data_url(image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
