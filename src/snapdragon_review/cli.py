from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .checks import scan
from .model import detect_runtime, review_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="snapdragon-review", description="Private local code and Vercel preflight checks")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="scan a project without uploading source")
    check.add_argument("path", nargs="?", default=".", type=Path)
    check.add_argument("--format", choices=("text", "json"), default="text")
    check.add_argument("--strict", action="store_true", help="exit non-zero for warnings as well as errors")
    runtime = subparsers.add_parser("runtime", help="report local ONNX Runtime/QNN availability")
    runtime.add_argument("--format", choices=("text", "json"), default="text")
    review = subparsers.add_parser("review", help="run an optional local model adapter on one file")
    review.add_argument("file", type=Path)
    review.add_argument("--adapter", required=True, type=Path, help="Python adapter defining review(prompt) -> str")
    review.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "runtime":
        status = detect_runtime()
        payload = {"available": status.available, "providers": status.providers, "message": status.message}
        if args.format == "json":
            print(json.dumps(payload, indent=2))
        else:
            print(("PASS" if status.available else "INFO") + f"  {status.message}")
        return 0 if status.available else 1

    if args.command == "review":
        try:
            file_path = args.file.resolve()
            root = file_path.parent
            findings = scan(root)
            result = review_file(
                args.adapter.resolve(),
                file_path.read_text(encoding="utf-8"),
                str(file_path),
                [finding.as_dict() for finding in findings if finding.path == file_path.name],
            )
            if args.format == "json":
                print(json.dumps({"file": str(file_path), "review": result}, indent=2))
            else:
                print(result)
        except (OSError, RuntimeError) as exc:
            print(f"ERROR   {exc}", file=sys.stderr)
            return 1
        return 0

    root = args.path.resolve()
    try:
        findings = scan(root)
    except NotADirectoryError as exc:
        print(f"ERROR   {exc}", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps({"root": str(root), "findings": [finding.as_dict() for finding in findings]}, indent=2))
    elif findings:
        for finding in findings:
            location = f":{finding.line}" if finding.line else ""
            print(f"{finding.severity.upper():7} {finding.path}{location} [{finding.rule}] {finding.message}")
        print(f"\n{len(findings)} finding(s) in {root}")
    else:
        print(f"PASS  No local preflight findings in {root}")
    has_blocking_findings = any(
        finding.severity == "error" or args.strict and finding.severity == "warning"
        for finding in findings
    )
    return 1 if has_blocking_findings else 0


if __name__ == "__main__":
    sys.exit(main())
