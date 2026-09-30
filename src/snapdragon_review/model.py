from __future__ import annotations

import json
import platform
from pathlib import Path
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeStatus:
    available: bool
    providers: tuple[str, ...] = ()
    message: str = ""


def detect_runtime() -> RuntimeStatus:
    """Report local ONNX Runtime providers without making them a hard dependency."""
    try:
        import onnxruntime as ort
    except ImportError:
        return RuntimeStatus(False, message="onnxruntime is not installed")

    providers = tuple(ort.get_available_providers())
    qnn = tuple(provider for provider in providers if "QNN" in provider.upper())
    if qnn:
        return RuntimeStatus(True, providers, f"QNN provider available: {', '.join(qnn)}")
    architecture = platform.machine()
    return RuntimeStatus(
        False,
        providers,
        "ONNX Runtime is installed, but no QNN provider is available "
        f"for this {architecture} Python environment; use a Qualcomm-compatible "
        "ARM64 Python/runtime build on the Snapdragon device.",
    )


def build_review_prompt(findings: list[dict[str, object]], source: str, file_name: str) -> str:
    """Build a bounded prompt for an optional local coding model."""
    return (
        "You are a local code review assistant. Do not invent issues. "
        "Return concise JSON with keys severity, title, explanation, remediation. "
        f"Review file {file_name} using these deterministic findings:\n"
        f"{json.dumps(findings, indent=2)}\nSource:\n{source[:12000]}"
    )


def review_file(
    model_path: Path,
    source: str,
    file_name: str,
    findings: list[dict[str, object]] | None = None,
) -> str:
    """Run a local Python model adapter when QNN is available."""
    status = detect_runtime()
    if not status.available:
        raise RuntimeError(status.message)
    try:
        import importlib.util

        spec = importlib.util.spec_from_file_location("snapdragon_local_model", model_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load model adapter: {model_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        reviewer: Any = getattr(module, "review", None)
        if not callable(reviewer):
            raise RuntimeError("Model adapter must define review(prompt: str) -> str")
        return str(reviewer(build_review_prompt(findings or [], source, file_name)))
    except OSError as exc:
        raise RuntimeError(f"Unable to load local model adapter: {exc}") from exc
