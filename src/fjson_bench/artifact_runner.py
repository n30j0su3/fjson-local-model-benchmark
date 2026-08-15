from dataclasses import asdict, dataclass
from pathlib import Path
import json
from .artifacts import ArtifactError, extract_html
from .qa_browser import run_browser_qa
from .qa_static import run_static_qa

@dataclass(frozen=True)
class ArtifactOutcome:
    challenge: str
    strict_path: str | None
    packaged_path: str | None
    repaired_path: str | None
    repair_attempts: int
    final_status: str
    qa_paths: tuple[str, ...]


def _write_raw(path: Path, result) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"text": result.text, "raw": result.raw}, ensure_ascii=False, sort_keys=True))


def _qa(path: Path, qa_root: Path, required_ids: list[str], interactions: list[dict[str, str]], min_mean_luminance: float | None = None) -> tuple[str, Path]:
    static = run_static_qa(path, required_ids)
    evidence = {"static": static, "browser": None}
    if static["status"] == "PASS":
        evidence["browser"] = run_browser_qa(path, qa_root / path.stem, interactions, min_mean_luminance=min_mean_luminance)
    status = "PASS" if static["status"] == "PASS" and evidence["browser"] and evidence["browser"]["status"] == "PASS" else "FAIL"
    evidence["status"] = status
    receipt = qa_root / f"{path.stem}.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(evidence, indent=2, sort_keys=True))
    return status, receipt


def run_artifact(provider, challenge: str, plan_prompt: str, build_prompt: str, repair_prompt: str, root: Path, required_ids: list[str], interactions: list[dict[str, str]], packager=None, min_mean_luminance: float | None = None) -> ArtifactOutcome:
    root = Path(root) / challenge
    raw_root = root / "raw"
    qa_root = root / "qa"
    plan = provider.chat([{"role": "user", "content": plan_prompt}], max_tokens=1024, temperature=0.0)
    _write_raw(raw_root / "plan.json", plan)
    build = provider.chat([{"role": "user", "content": build_prompt}], max_tokens=16384, temperature=0.0)
    _write_raw(raw_root / "build.json", build)
    strict_path = root / "strict" / "index.html"
    strict_path.parent.mkdir(parents=True, exist_ok=True)
    failures = []
    qa_paths = []
    try:
        strict_path.write_text(extract_html(build.text))
        qa_candidate = strict_path
        packaged_path = strict_path
        if packager is not None:
            packaged_path = root / "packaged" / "index.html"
            qa_candidate = packager(strict_path, packaged_path)
        status, receipt = _qa(qa_candidate, qa_root, required_ids, interactions, min_mean_luminance)
        qa_paths.append(str(receipt))
        if status == "PASS":
            return ArtifactOutcome(challenge, str(strict_path), str(packaged_path), None, 0, "PASS", tuple(qa_paths))
        evidence = json.loads(receipt.read_text())
        failures = list(evidence["static"]["failures"])
        browser = evidence.get("browser") or {}
        failures.extend(browser.get("failures", []))
        for viewport in browser.get("viewports", []):
            failures.extend(viewport.get("failures", []))
            if not viewport.get("interaction_pass", True):
                failures.append({"code": "INTERACTION", "width": viewport.get("width")})
            if viewport.get("horizontal_overflow"):
                failures.append({"code": "HORIZONTAL_OVERFLOW", "width": viewport.get("width")})
        failures.extend({"code": "CONSOLE_ERROR", "detail": item} for item in browser.get("console_errors", []))
        failures.extend({"code": "BLOCKED_REQUEST", "url": item} for item in browser.get("blocked_requests", []))
    except ArtifactError as error:
        failures = [{"code": "HTML_EXTRACT", "detail": str(error)}]
    repair_text = repair_prompt + "\nBUILD_CONTRACT::\n" + build_prompt + "\nFAILURES::" + json.dumps(failures) + "\nORIGINAL::\n" + build.text
    repair = provider.chat([{"role": "user", "content": repair_text}], max_tokens=16384, temperature=0.0)
    _write_raw(raw_root / "repair.json", repair)
    repaired_path = root / "repaired" / "index.html"
    repaired_path.parent.mkdir(parents=True, exist_ok=True)
    repaired_candidate = repaired_path
    try:
        repaired_path.write_text(extract_html(repair.text))
        if packager is not None:
            repaired_candidate = packager(repaired_path, root / "repaired-packaged" / "index.html")
        status, receipt = _qa(repaired_candidate, qa_root, required_ids, interactions, min_mean_luminance)
        qa_paths.append(str(receipt))
    except ArtifactError:
        status = "FAIL"
    return ArtifactOutcome(challenge, str(strict_path) if strict_path.exists() else None, str(repaired_candidate) if status == "PASS" else None, str(repaired_path) if repaired_path.exists() else None, 1, status, tuple(qa_paths))
