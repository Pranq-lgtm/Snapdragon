# Demo script

## 90-second flow

1. Show a local project containing `vercel.json` and a deliberately unsafe token fixture.
2. Run:

   ```powershell
   snapdragon-review check . --format json
   ```

3. Point out the secret and insecure rewrite findings. Explain that the output was generated without an API key or network request.
4. Run:

   ```powershell
   snapdragon-review runtime --format json
   ```

5. On the Snapdragon ARM64 machine, show `QNNExecutionProvider` in the provider list.
6. Start a local build or test process beside the review command. Explain that model inference is assigned to the NPU, leaving CPU capacity for the build.
7. Run the optional model review:

   ```powershell
   snapdragon-review review src\app.ts --adapter .\local_model_adapter.py --format json
   ```

8. End with the privacy boundary: code remains on the laptop from pre-commit through review.
