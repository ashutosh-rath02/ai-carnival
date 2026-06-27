"""Document-extraction runners for the AI OCR Field Test.

Each runner implements the BaseRunner interface (see base.py) and returns a
consistent result dict so the experiment CLI can treat every model the same way.
"""

from .base import BaseRunner, build_result

# Registry of available runners, keyed by the name used on the CLI (--models ...).
# Runner classes are imported lazily inside get_runner() so that a missing heavy
# dependency (e.g. paddleocr) does not break the whole package import.

AVAILABLE_RUNNERS = ["paddleocr", "vlm", "mistral_ocr", "unlimited_ocr"]


def get_runner(name: str) -> BaseRunner:
    """Instantiate a runner by its CLI name. Imports are lazy on purpose."""
    key = name.strip().lower()
    if key == "paddleocr":
        from .paddleocr_runner import PaddleOCRRunner
        return PaddleOCRRunner()
    if key == "vlm":
        from .vlm_runner import VLMRunner
        return VLMRunner()
    if key == "mistral_ocr":
        from .mistral_ocr_runner import MistralOCRRunner
        return MistralOCRRunner()
    if key == "unlimited_ocr":
        from .unlimited_ocr_runner import UnlimitedOCRRunner
        return UnlimitedOCRRunner()
    raise ValueError(
        f"Unknown runner '{name}'. Available: {', '.join(AVAILABLE_RUNNERS)}"
    )


__all__ = ["BaseRunner", "build_result", "get_runner", "AVAILABLE_RUNNERS"]
