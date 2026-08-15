from pathlib import Path
import pytest
pytest.importorskip("playwright.sync_api")
from fjson_bench.qa_browser import run_browser_qa
from fjson_bench.report import generate_report


def test_generated_report_is_browser_clean_at_three_viewports(tmp_path):
    report = generate_report(Path("tests/fixtures/results/pass.json"), tmp_path / "report")
    result = run_browser_qa(report, tmp_path / "browser", [])
    assert result["status"] == "PASS"
    assert [row["width"] for row in result["viewports"]] == [1600, 768, 480]
    assert result["console_errors"] == []
