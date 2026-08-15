# FJSON Local Model Benchmark

Reproducible, local-first evaluation of OpenAI-compatible and Ollama models. The runner measures runtime behavior, asks every model to build the same three browser artifacts, validates them at three viewports, and produces an offline evidence report.

> **Evidence over leaderboards.** Runtime, technical quality, browser QA and human utility remain separate dimensions. Missing data is reported as unavailable, never guessed.

## What every full run builds

1. **Editorial visual** — a polished single-file HTML experience.
2. **Synthetic ecommerce dashboard** — deterministic fixture data; no client data.
3. **Original medieval Three.js scene** — pinned `three@0.160.0`, bundled offline under its MIT license.
4. **Offline report** — `results.json`, `manifest.json`, and `report/index.html` work with `file://` and contain no CDN dependency.
5. **Editorial kit** — evidence-bound claims, walkthrough, Short script, article brief, shotlist, conclusions and FJSON Studio prompts.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/playwright install chromium
cp config/examples/miniv.json config/local/miniv.json
.venv/bin/benchctl run --config config/local/miniv.json --preset full-editorial
```

Presets:

- `speed`: three runtime repetitions.
- `quality`: runtime plus three browser artifacts.
- `full-editorial`: quality gates, offline SPA and editorial kit.

The local config directory and all `runs/` are Git-ignored.

## Provider configuration

OpenAI-compatible / llama.cpp:

```json
{
  "provider": "openai-compatible",
  "model": "your-model-alias",
  "endpoint": "http://127.0.0.1:9161/v1"
}
```

Ollama uses `"provider": "ollama"` and its OpenAI-independent `/api/chat` base endpoint. API keys are referenced through environment variables; never commit them.

## Run structure

```text
runs/<run-id>/
├── events.jsonl
├── metrics/
├── deliverables/
│   ├── d1-visual/
│   ├── d2-ecommerce/
│   └── d3-threejs/
├── editorial/
├── results.json
├── manifest.json
├── receipt.json
└── report/index.html
```

Failures remain failures. Raw responses and partial reports are preserved locally for diagnosis.

## QA and tests

```bash
PYTHONPATH=src .venv/bin/pytest -q
```

Browser gates run at **1600 px**, **768 px**, and **480 px**. They check required controls, interactions, overflow, page errors, console errors and attempted external requests. Static QA also checks HTML structure, JavaScript syntax and network-capable code.

## Publishing model

Publication is deliberately two-step:

```bash
# No files are copied; hashes and policy findings are printed.
benchctl publish-pack --run runs/<run-id> --destination /tmp/public-pack --dry-run

# Only after human approval bound to the dry-run fingerprint:
benchctl publish-pack --run runs/<run-id> --destination benchmarks/<model>/<run-id> --approval approval.json
```

The public allowlist excludes raw/strict model responses. It blocks symlinks, path escapes, oversized files, private topology, home paths, bearer-like tokens and private-key material.

> **Status semantics:** `PASS` means the run satisfied its declared static and browser contracts at 1600/768/480 px. It is not an aesthetic endorsement. Public gallery export still requires human visual review and an N30 approval file bound to the dry-run fingerprint.

## n8n one-click wrapper

`workflows/n8n/miniv-local-model-benchmark.json` is an inactive, importable thin wrapper. It calls the host bridge over Docker's `host.docker.internal`; benchmark logic remains in this repository.

The bridge defaults to loopback-only. The included systemd unit is a production example for an installation at `/opt/fjson-local-model-benchmark`: copy `config/examples/bridge.env` to `/etc/fjson-bench/bridge.env`, set the exact Docker CIDR, install the unit under `/etc/systemd/system/`, then enable it with `sudo systemctl enable --now fjson-benchmark-bridge`. For a user-local installation, adapt those paths in a private unit outside the repository.

- non-allowlisted host/LAN requests return `403`;
- the n8n container receives `200` from `/health`;
- the workflow remains inactive until operator review.

## Architecture

```text
benchctl / n8n
      │
      ▼
validated RunSpec ── PID lock ── append-only ledger
      │
      ├── provider adapter ── local model endpoint
      ├── runtime repetitions
      ├── artifact plan/build/one-repair
      ├── static + browser QA (network blocked)
      ├── offline report + editorial kit
      └── fail-closed public pack ── optional Gallery export
```

## Design principles

- Local-first and serial: one large model at a time.
- Reproducible prompts and pinned browser dependency.
- Synthetic ecommerce data only.
- No unsupported comparative claims.
- No single score that hides trade-offs.
- Human approval before public benchmark export.

## License

Apache-2.0. The vendored Three.js runtime is MIT-licensed; its license and SHA-256 manifest are included under `vendor/three/`.
