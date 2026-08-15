from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import os
from .artifact_runner import run_artifact
from .artifacts import ArtifactError
from .contracts import RunSpec, RunState
from .editorial import write_editorial_kit
from .ledger import RunLedger
from .lock import RunLock
from .presets import load_preset
from .promptset import load_promptset
from .providers.fake import FakeProvider
from .providers.ollama import OllamaProvider
from .providers.openai_compat import OpenAICompatibleProvider
from .report import generate_report
from .speed import run_speed
from .three_pack import ThreePackError, inline_three

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _provider(config):
    kind = config["provider"]
    if kind == "fake":
        return FakeProvider.from_file(config["fixture"])
    endpoint = config.get("endpoint") or os.environ[config["endpoint_env"]]
    key = os.environ.get(config.get("api_key_env", "")) or None
    if kind in {"openai-compatible", "llama.cpp"}:
        return OpenAICompatibleProvider(endpoint, config["model"], key)
    if kind == "ollama":
        return OllamaProvider(endpoint, config["model"])
    raise ValueError(f"unsupported provider: {kind}")


def _relative(value, root):
    if value is None:
        return None
    return str(Path(value).resolve().relative_to(root.resolve()))


def _outcome_dict(outcome, root):
    data = asdict(outcome)
    for key in ("strict_path", "packaged_path", "repaired_path"):
        data[key] = _relative(data[key], root)
    data["qa_paths"] = [_relative(path, root) for path in data["qa_paths"]]
    return data


def _hash_manifest(root):
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            files[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {"version": 1, "files": files}


def package_three_source(source: Path, destination: Path) -> Path:
    try:
        return inline_three(source, PROJECT_ROOT / "vendor" / "three", destination)
    except ThreePackError as error:
        raise ArtifactError(str(error)) from error


def execute_run(config_path, preset_name, provider_override=None, model_override=None):
    config = json.loads(Path(config_path).read_text())
    if provider_override:
        config["provider"] = provider_override
    if model_override:
        config["model"] = model_override
    runs_root = Path(config.get("runs_root", PROJECT_ROOT / "runs"))
    runs_root.mkdir(parents=True, exist_ok=True)
    spec = RunSpec(config["provider"], config["model"], preset_name)
    run_id = spec.run_id()
    run_root = runs_root / run_id
    ledger = RunLedger.create(run_root, run_id)
    lock = RunLock(runs_root / ".benchmark.lock", run_id)
    results = {"run_id": run_id, "state": "PENDING", "model": {"id": config["model"]}, "configuration": {"provider": config["provider"], "preset": preset_name}, "speed": {}, "context": {"max_verified": None, "provenance": "unavailable"}, "artifacts": [], "qa": {}, "editorial": {}, "evidence": ["events.jsonl"], "recommendations": [], "failures": []}
    lock.acquire()
    try:
        provider = _provider(config)
        ledger.transition(RunState.PREFLIGHT, {"health": provider.health(), "model": provider.model_identity()})
        ledger.transition(RunState.RUNNING)
        preset = load_preset(PROJECT_ROOT / "presets" / f"{preset_name}.json")
        speed = run_speed(provider, preset, run_root / "metrics" / "speed-raw")
        (run_root / "metrics").mkdir(exist_ok=True)
        (run_root / "metrics/speed.json").write_text(json.dumps(speed, indent=2))
        results["speed"] = speed["summary"]
        results["speed"]["decode_tps"]["evidence_path"] = "metrics/speed.json"
        if preset.get("artifacts"):
            prompts = load_promptset(PROJECT_ROOT / "prompts/v1")
            repair = prompts["repair.txt"].text
            challenges = [
                ("d1-visual", "d1-visual-plan.txt", "d1-visual-build.txt", ["app", "nav-overview", "nav-metrics", "theme-toggle", "theme-status"], [{"selector": "#theme-toggle", "expect": "#theme-status", "value": "theme-dark"}], None),
                ("d2-ecommerce", "d2-ecommerce-plan.txt", "d2-ecommerce-build.txt", ["store-filter", "channel-filter", "kpi-revenue", "chart-sales", "insights"], [{"selector": "#store-filter", "expect": "#insights", "value": "filtered"}], None),
                ("d3-threejs", "d3-threejs-plan.txt", "d3-threejs-build.txt", ["scene", "reset-camera", "quality-toggle", "scene-status"], [{"selector": "#quality-toggle", "expect": "#scene-status", "value": "quality-high"}], package_three_source),
            ]
            for challenge, plan_name, build_name, ids, interactions, packager in challenges:
                outcome = run_artifact(provider, challenge, prompts[plan_name].text, prompts[build_name].text, repair, run_root / "deliverables", ids, interactions, packager)
                results["artifacts"].append(_outcome_dict(outcome, run_root))
        ledger.transition(RunState.QA)
        artifact_pass = all(item["final_status"] == "PASS" for item in results["artifacts"])
        results["qa"] = {"status": "PASS" if artifact_pass else "FAIL", "viewports": [1600, 768, 480]}
        ledger.transition(RunState.REPORTING)
        results["state"] = "PASS" if artifact_pass else "FAIL"
        if preset.get("editorial"):
            paths = write_editorial_kit(run_root, results)
            results["editorial"] = {"files": [str(path.relative_to(run_root)) for path in paths]}
        results["recommendations"] = ["Use only for local work matching the verified artifact and runtime gates."]
        (run_root / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
        generate_report(run_root / "results.json", run_root / "report")
        (run_root / "manifest.json").write_text(json.dumps(_hash_manifest(run_root), indent=2, sort_keys=True))
        final_state = RunState.PASS if results["state"] == "PASS" else RunState.FAIL
        ledger.transition(final_state, {"results": "results.json", "report": "report/index.html"})
        receipt = {"run_id": run_id, "status": results["state"], "run_root": str(run_root), "report": str(run_root / "report/index.html")}
        (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2))
        (runs_root / "latest.json").write_text(json.dumps(receipt, indent=2))
        return receipt
    except Exception as error:
        results["state"] = "FAIL"
        results["failures"].append({"code": type(error).__name__, "detail": str(error)})
        (run_root / "results.json").write_text(json.dumps(results, indent=2, sort_keys=True))
        generate_report(run_root / "results.json", run_root / "report")
        try:
            ledger.transition(RunState.FAIL, {"error": type(error).__name__})
        except ValueError:
            pass
        receipt = {"run_id": run_id, "status": "FAIL", "run_root": str(run_root), "report": str(run_root / "report/index.html"), "error": str(error)}
        (run_root / "receipt.json").write_text(json.dumps(receipt, indent=2))
        (runs_root / "latest.json").write_text(json.dumps(receipt, indent=2))
        return receipt
    finally:
        lock.release()
