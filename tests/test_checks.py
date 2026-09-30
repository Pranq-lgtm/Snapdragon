import json

from snapdragon_review.checks import scan
from snapdragon_review.model import build_review_prompt


def test_detects_secret_and_invalid_vercel_config(tmp_path):
    secret = "12345678" + "90123456"
    (tmp_path / "app.py").write_text(f'TOKEN = "{secret}"\n', encoding="utf-8")
    (tmp_path / "vercel.json").write_text("{broken", encoding="utf-8")

    findings = scan(tmp_path)

    assert {finding.rule for finding in findings} == {"secret-detected", "invalid-vercel-json"}


def test_accepts_valid_build_configuration(tmp_path):
    (tmp_path / "package.json").write_text(json.dumps({"scripts": {"build": "next build"}}), encoding="utf-8")
    (tmp_path / "vercel.json").write_text(json.dumps({"framework": "nextjs"}), encoding="utf-8")

    assert scan(tmp_path) == []


def test_detects_unignored_env_and_insecure_rewrite(tmp_path):
    (tmp_path / ".env").write_text("DATABASE_URL=local", encoding="utf-8")
    (tmp_path / "vercel.json").write_text(
        json.dumps({"rewrites": [{"source": "/api/:path*", "destination": "http://internal.local/:path*"}]}),
        encoding="utf-8",
    )

    findings = scan(tmp_path)

    assert {finding.rule for finding in findings} == {"unignored-env-file", "insecure-vercel-rewrite"}


def test_build_review_prompt_is_bounded():
    prompt = build_review_prompt([], "x" * 20_000, "app.py")

    assert "app.py" in prompt
    assert len(prompt) < 13_000


def test_build_review_prompt_includes_deterministic_findings():
    prompt = build_review_prompt(
        [{"rule": "secret-detected", "severity": "error"}],
        "source",
        "app.py",
    )

    assert "secret-detected" in prompt


def test_runtime_reports_installed_providers():
    from snapdragon_review.model import detect_runtime

    status = detect_runtime()

    assert isinstance(status.providers, tuple)
    assert status.message
