# Snapdragon Local Review

A private, offline-first CLI for catching code and Vercel deployment issues before they leave a developer's machine.

## Quick start

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
snapdragon-review check .
```

The command exits with status `1` when it finds errors, making it suitable for pre-commit hooks and CI. Add `--strict` to treat warnings as failures. Use `--format json` for editor or automation integrations.

## Checks included

- Leaked secrets in tracked-looking files
- Dangerous wildcard CORS and debug settings
- Vercel configuration issues such as unsupported build output settings
- Missing project metadata and common deployment footguns

The deterministic checks never upload source code. They run by default without third-party dependencies.

## Local model review

Check the hardware/runtime boundary with:

```powershell
snapdragon-review runtime
snapdragon-review runtime --format json
```

The optional `review` command requires an external local Python adapter exposing
`review(prompt: str) -> str` and an ONNX Runtime installation with a QNN
provider:

```powershell
snapdragon-review review src\app.ts --adapter .\local_model_adapter.py --format json
```

No cloud fallback is used. If QNN is unavailable, the command exits non-zero
and explains what must be installed.

The QNN extra installs the Qualcomm-enabled runtime:

```powershell
python -m pip install -e ".[qnn]"
```

QNN availability depends on the interpreter architecture. On a Snapdragon
Windows device, use an ARM64 Python environment; an AMD64 interpreter may
install successfully but expose only CPU/Azure providers.

Copy [local_model_adapter.py.example](C:/Users/neela/Snapdragon/local_model_adapter.py.example)
to `local_model_adapter.py`, install the adapter's tokenizer dependency, and
place an offline ONNX model under `models\code-review` (or set
`SNAPDRAGON_MODEL`). The model must be exported with input names accepted by
the tokenizer output.

## Pre-commit

```yaml
repos:
  - repo: local
    hooks:
      - id: snapdragon-review
        name: Snapdragon local review
        entry: snapdragon-review check .
        language: system
        pass_filenames: false
```

## Snapdragon NPU direction

Install the platform-specific ONNX Runtime/QNN build separately, then provide a local adapter file. The adapter owns model-specific tokenization and inference; the CLI supplies bounded source plus deterministic findings. The CLI keeps deterministic checks usable on every machine and enables model inference only when the local runtime is available.
