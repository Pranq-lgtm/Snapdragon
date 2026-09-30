# Architecture

```text
Developer repository
        |
        v
snapdragon-review CLI
        |
        +--> deterministic checks
        |      +--> secret patterns
        |      +--> package.json build checks
        |      +--> vercel.json security/deployment checks
        |      +--> text or JSON findings
        |
        +--> optional local model adapter
               |
               +--> tokenizer + local ONNX/GenAI model
               |
               +--> ONNX Runtime
                       |
                       +--> QNN Execution Provider
                               |
                               +--> Hexagon NPU / HTP

No source upload, API key, or cloud inference path.
```

## Runtime modes

| Mode | Runtime | Privacy | Purpose |
|---|---|---|---|
| `check` | Python standard library | Fully local | Fast deterministic preflight |
| `review --backend transformers` | Local Transformers model | Fully local | Compatibility fallback |
| `review --backend qnn` | ONNX Runtime QNN | Fully local | Snapdragon NPU acceleration |

The current adapter boundary is intentionally explicit: if the QNN provider is not present, the command reports the problem instead of silently using a remote service.

## Deployment requirements

- Windows on ARM64 Snapdragon device
- ARM64 Python environment
- `onnxruntime-qnn`
- Local ONNX Runtime GenAI-compatible code model
- Tokenizer and model files stored outside Git
