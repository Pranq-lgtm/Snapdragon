from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str
    message: str
    path: str
    line: int | None = None

    def as_dict(self) -> dict[str, object]:
        return {
            "rule": self.rule,
            "severity": self.severity,
            "message": self.message,
            "path": self.path,
            "line": self.line,
        }


_SECRET_PATTERNS = (
    ("AWS access key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("generic secret", re.compile(r"(?i)(api[_-]?key|secret|token)\s*[=:]\s*['\"][^'\"]{12,}['\"]")),
)
_IGNORED_DIRECTORIES = {".git", ".venv", "node_modules", ".next", "dist", "build", "__pycache__"}


def _relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _text_files(root: Path) -> Iterator[tuple[Path, str]]:
    for path in root.rglob("*"):
        if (
            path.is_file()
            and not _IGNORED_DIRECTORIES.intersection(path.parts)
            and path.stat().st_size <= 1_000_000
        ):
            try:
                yield path, path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue


def scan(root: Path) -> list[Finding]:
    if not root.is_dir():
        raise NotADirectoryError(f"Project path does not exist or is not a directory: {root}")

    findings: list[Finding] = []
    for path, text in _text_files(root):
        relative = _relative(root, path)
        for line_number, line in enumerate(text.splitlines(), 1):
            for label, pattern in _SECRET_PATTERNS:
                if pattern.search(line) and not relative.endswith((".example", ".sample")):
                    findings.append(Finding("secret-detected", "error", f"Possible {label} found in source", relative, line_number))
                    break

    package_json = root / "package.json"
    if package_json.exists():
        try:
            package = json.loads(package_json.read_text(encoding="utf-8"))
            scripts = package.get("scripts", {})
            if not isinstance(scripts, dict) or not any(name in scripts for name in ("build", "vercel-build")):
                findings.append(Finding("missing-build-script", "warning", "package.json has no build or vercel-build script", "package.json"))
        except json.JSONDecodeError:
            findings.append(Finding("invalid-package-json", "error", "package.json is not valid JSON", "package.json"))

    env_file = root / ".env"
    if env_file.exists():
        findings.append(Finding("unignored-env-file", "error", ".env should not be committed; use environment settings in the deployment platform", ".env"))

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            pyproject.read_text(encoding="utf-8")
        except OSError as exc:
            findings.append(Finding("unreadable-project-file", "error", f"Unable to read pyproject.toml: {exc}", "pyproject.toml"))

    vercel = root / "vercel.json"
    if vercel.exists():
        try:
            config = json.loads(vercel.read_text(encoding="utf-8"))
            if config.get("builds") and config.get("buildCommand"):
                findings.append(Finding("conflicting-vercel-build", "warning", "vercel.json mixes legacy builds with buildCommand", "vercel.json"))
            if config.get("headers") and "*" in json.dumps(config["headers"]):
                findings.append(Finding("wildcard-security-header", "warning", "Review wildcard Vercel headers before deployment", "vercel.json"))
            if config.get("rewrites") and any(
                isinstance(rule, dict) and str(rule.get("destination", "")).startswith("http://")
                for rule in config["rewrites"]
            ):
                findings.append(Finding("insecure-vercel-rewrite", "error", "Vercel rewrites should not proxy over plain HTTP", "vercel.json"))
        except json.JSONDecodeError:
            findings.append(Finding("invalid-vercel-json", "error", "vercel.json is not valid JSON", "vercel.json"))

    return findings
