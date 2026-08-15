import json
from pathlib import Path
from fjson_bench.cli import main


def test_full_fake_cli_run_and_publish_dry_run(tmp_path):
    config = {
        "provider": "fake",
        "model": "fixture-model",
        "fixture": str(Path("tests/fixtures/fake_full_responses.json").resolve()),
        "runs_root": str(tmp_path / "runs"),
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config))
    assert main(["run", "--config", str(config_path), "--preset", "full-editorial"]) == 0
    latest = json.loads((tmp_path / "runs/latest.json").read_text())
    run = tmp_path / "runs" / latest["run_id"]
    assert json.loads((run / "results.json").read_text())["state"] == "PASS"
    assert (run / "report/index.html").exists()
    assert len(list((run / "deliverables").glob("*/strict/index.html"))) == 3
    d1=json.loads((run/"deliverables/d1-visual/qa/index.json").read_text())
    d2=json.loads((run/"deliverables/d2-ecommerce/qa/index.json").read_text())
    d3=json.loads((run/"deliverables/d3-threejs/qa/index.json").read_text())
    assert d1["browser"]["minimum_mean_luminance"] is None
    assert d2["browser"]["minimum_mean_luminance"] is None
    assert d3["browser"]["minimum_mean_luminance"]==6.0
    assert len(list((run / "editorial").glob("*"))) == 7
    assert main(["publish-pack", "--run", str(run), "--destination", str(tmp_path / "pack"), "--dry-run"]) == 0
    assert not (tmp_path / "pack").exists()
