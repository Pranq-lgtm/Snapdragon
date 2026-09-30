# Snapdragon Local Review — Submission Content

## Project title

**Snapdragon Local Review: Private NPU-Powered Code & Vercel Preflight**

## Brief project description

Snapdragon Local Review is an offline-first developer assistant that catches secrets, deployment misconfigurations, and security issues before code reaches Vercel. It runs deterministic checks locally and can optionally send bounded source context to a locally hosted coding model. On Snapdragon Windows ARM64 systems, the model is designed to use ONNX Runtime with the Qualcomm QNN Execution Provider so review inference runs on the Hexagon NPU while the CPU remains available for builds, containers, and development servers. No source code, API key, or proprietary context leaves the device.

## Technical implementation

The product is a Python CLI that integrates with pre-commit and CI workflows:

1. The developer runs `snapdragon-review check .` locally.
2. Deterministic rules inspect source files, `.env` exposure, `package.json`, and `vercel.json`.
3. Findings are emitted as human-readable text or structured JSON.
4. An optional local model adapter receives only bounded source context and deterministic findings.
5. The Snapdragon deployment uses an ARM64 Python environment, `onnxruntime-qnn`, an ONNX/ONNX Runtime GenAI export of a small code model such as Qwen2.5-Coder-1.5B-Instruct, and the QNN Execution Provider.
6. The command fails closed when QNN is unavailable; it never silently falls back to a cloud provider.

## Application use case and innovation

Developers currently choose between slow manual review and cloud AI tools that can expose proprietary code. This project moves the first review loop to the edge: instant feedback, offline operation, and local governance. The innovation is not only “AI on a laptop”; it is workload separation. The NPU handles model inference while the CPU remains available for the developer’s compiler, Docker containers, local server, and test suite.

## Deployment and accessibility

The deterministic scanner works on any Python 3.10+ machine without third-party runtime dependencies. Snapdragon users can install the QNN extra and provide a local ONNX model. The same CLI supports:

```powershell
snapdragon-review check . --strict --format json
snapdragon-review runtime --format json
snapdragon-review review src\app.ts --adapter .\local_model_adapter.py --format json
```

The project is designed for air-gapped or governance-sensitive environments. Model files are local and excluded from version control.

## Presentation and demonstration plan

The demo compares two runs on the same project:

- **Baseline:** an intentionally unsafe Vercel project containing a leaked token and an HTTP rewrite.
- **Snapdragon Local Review:** findings appear immediately, with no network request; optional model inference is shown while CPU utilization remains available for the build.

The presentation includes the architecture, setup steps, threat model, workflow, measured checks, and roadmap.

## Expected impact

- Reduce accidental secret and deployment misconfiguration leaks.
- Give developers a private review loop before staging.
- Preserve CPU responsiveness during local builds.
- Make local AI practical for enterprise code-governance policies.
