"""VLM runner — vision LLM that extracts structured document fields.

Supports two providers, switchable via the ``VLM_PROVIDER`` env var:
  - ``gemini`` (default)  -> google-generativeai, needs GEMINI_API_KEY
  - ``openai``            -> OpenAI vision, needs OPENAI_API_KEY

The extraction prompt lives in ``prompts/vlm_extraction_prompt.txt``. Output is
saved as ``outputs/vlm/{test_id}_output.json``.

If the relevant API key is missing, the runner writes a stub JSON file with setup
instructions and reports ``failed`` (so the run log makes clear no real
extraction happened) without crashing the rest of the experiment.
"""

from __future__ import annotations

import base64
import io
import json
import os

from .base import BaseRunner, test_id_from_path
from .pdf_utils import load_images

# Latest vision models as of this run (override via VLM_MODEL in .env).
# Gemini 3.5 Flash is the newest Flash; GPT-5.5 is the newest OpenAI flagship.
DEFAULT_MODELS = {
    "gemini": "gemini-3.5-flash",
    "openai": "gpt-5.5",
}

PROMPT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "prompts", "vlm_extraction_prompt.txt"
)


class VLMRunner(BaseRunner):
    name = "vlm"
    output_subdir = "vlm"

    def __init__(self, max_pages: int = 10):
        _load_dotenv()
        self.provider = (os.getenv("VLM_PROVIDER") or "gemini").strip().lower()
        self.model = (os.getenv("VLM_MODEL") or "").strip() or DEFAULT_MODELS.get(
            self.provider, ""
        )
        self.max_pages = max_pages
        self.prompt = _read_prompt()

    # -- provider dispatch ---------------------------------------------------

    def extract(self, input_path: str, output_dir: str) -> str:
        test_id = test_id_from_path(input_path)
        out_path = os.path.join(output_dir, f"{test_id}_output.json")

        api_key = self._api_key()
        if not api_key:
            _write_stub(out_path, self.provider)
            raise RuntimeError(
                f"{self._key_name()} not configured "
                f"(wrote setup stub to {out_path})"
            )

        images = load_images(input_path)[: self.max_pages]

        if self.provider == "gemini":
            raw = self._call_gemini(api_key, images)
        elif self.provider == "openai":
            raw = self._call_openai(api_key, images)
        else:
            raise ValueError(
                f"Unknown VLM_PROVIDER '{self.provider}'. Use 'gemini' or 'openai'."
            )

        payload = _coerce_json(raw)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        return out_path

    # -- providers -----------------------------------------------------------

    def _call_gemini(self, api_key: str, images) -> str:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(self.model or DEFAULT_MODELS["gemini"])
        response = model.generate_content([self.prompt, *images])
        return response.text

    def _call_openai(self, api_key: str, images) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        content = [{"type": "text", "text": self.prompt}]
        for image in images:
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": _to_data_url(image)},
                }
            )
        response = client.chat.completions.create(
            model=self.model or DEFAULT_MODELS["openai"],
            messages=[{"role": "user", "content": content}],
        )
        return response.choices[0].message.content

    # -- helpers -------------------------------------------------------------

    def _key_name(self) -> str:
        return "OPENAI_API_KEY" if self.provider == "openai" else "GEMINI_API_KEY"

    def _api_key(self) -> str:
        return (os.getenv(self._key_name()) or "").strip()


def _read_prompt() -> str:
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except FileNotFoundError:
        # Minimal inline fallback so the runner still works if the file is moved.
        return (
            "Extract all visible text from this document and return structured "
            "JSON with document fields. Use null for unclear values. Do not invent "
            "values."
        )


def _to_data_url(image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _coerce_json(raw: str):
    """Parse the model's reply into a JSON object, tolerating code fences/prose.

    If parsing fails, preserve the raw text so nothing is lost on review.
    """
    if raw is None:
        return {"raw_response": "", "parse_error": "empty response"}
    text = raw.strip()
    if text.startswith("```"):
        # Strip a ```json ... ``` fence.
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    # Narrow to the outermost JSON object if there is surrounding prose.
    start, end = text.find("{"), text.rfind("}")
    candidate = text[start : end + 1] if start != -1 and end != -1 else text
    try:
        return json.loads(candidate)
    except (json.JSONDecodeError, ValueError):
        return {"raw_response": raw, "parse_error": "model did not return valid JSON"}


def _write_stub(out_path: str, provider: str) -> None:
    key_name = "OPENAI_API_KEY" if provider == "openai" else "GEMINI_API_KEY"
    stub = {
        "status": "not_configured",
        "provider": provider,
        "message": f"No {key_name} found. Add it to your .env file to enable the VLM runner.",
        "how_to_fix": [
            f"1. Copy .env.example to .env",
            f"2. Set {key_name}=<your key>",
            "3. Optionally set VLM_PROVIDER (gemini|openai) and VLM_MODEL",
            "4. Re-run: python scripts/run_experiment.py --models vlm",
        ],
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(stub, fh, ensure_ascii=False, indent=2)


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
