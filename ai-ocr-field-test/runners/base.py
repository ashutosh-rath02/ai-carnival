"""Base runner interface shared by every extractor.

A runner takes one input document and produces one raw output file, returning a
structured result dict so the experiment CLI can log every model identically.
"""

from __future__ import annotations

import os
import re
import time
from typing import Optional


def test_id_from_path(input_path: str) -> str:
    """Derive a test id from a filename.

    'T3_rotated_invoice.jpg' -> 'T3'. Falls back to the full stem if there is no
    leading T<number> token (so arbitrary filenames still work).
    """
    stem = os.path.splitext(os.path.basename(input_path))[0]
    match = re.match(r"(T\d+)", stem, flags=re.IGNORECASE)
    return match.group(1).upper() if match else stem


def build_result(
    model: str,
    input_file: str,
    output_file: Optional[str],
    latency_sec: float,
    status: str,
    error: Optional[str] = None,
) -> dict:
    """Construct the standard result dict every runner must return."""
    return {
        "model": model,
        "input_file": input_file,
        "output_file": output_file,
        "latency_sec": round(float(latency_sec), 3),
        "status": status,
        "error": error,
    }


class BaseRunner:
    """Interface for all runners.

    Subclasses set ``name`` and implement ``extract()``. The public ``run()``
    method handles the boilerplate that every runner shares: making the output
    directory, timing the call, and converting exceptions into a clean
    ``status='failed'`` result instead of crashing the whole experiment.
    """

    name: str = "base"
    output_subdir: str = "base"

    def run(self, input_path: str, output_dir: str) -> dict:
        """Run extraction on one document and return a structured result dict."""
        os.makedirs(output_dir, exist_ok=True)
        start = time.perf_counter()
        try:
            output_file = self.extract(input_path, output_dir)
            latency = time.perf_counter() - start
            return build_result(
                model=self.name,
                input_file=input_path,
                output_file=output_file,
                latency_sec=latency,
                status="success",
                error=None,
            )
        except Exception as exc:  # noqa: BLE001 - failures must never crash the run
            latency = time.perf_counter() - start
            return build_result(
                model=self.name,
                input_file=input_path,
                output_file=None,
                latency_sec=latency,
                status="failed",
                error=f"{type(exc).__name__}: {exc}",
            )

    def extract(self, input_path: str, output_dir: str) -> str:
        """Do the actual extraction and write the raw output file.

        Must return the path of the written output file. Raise on failure; the
        ``run()`` wrapper turns exceptions into a ``failed`` result.
        """
        raise NotImplementedError
