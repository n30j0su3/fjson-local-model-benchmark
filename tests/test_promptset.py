from pathlib import Path
from fjson_bench.promptset import load_prompt, load_promptset

def test_promptset_is_complete_and_stable():
    assets=load_promptset(Path("prompts/v1")); assert len(assets)==8
    assert all(len(a.sha256)==64 for a in assets.values())
    assert load_prompt(Path("prompts/v1/system.txt")).sha256==assets["system.txt"].sha256

def test_fixture_is_synthetic_and_sanitized():
    text=Path("fixtures/ecommerce-synthetic.json").read_text(); assert '"synthetic": true' in text and "maaji" not in text.lower()

def test_build_prompts_declare_exact_interaction_contracts():
    root=Path("prompts/v1")
    d1=(root/"d1-visual-build.txt").read_text(); d2=(root/"d2-ecommerce-build.txt").read_text(); d3=(root/"d3-threejs-build.txt").read_text()
    assert '#theme-status` must become exactly `theme-dark' in d1 and "4.5:1" in d1 and "14,000 characters" in d1
    assert '#insights` must become exactly `filtered' in d2 and "four KPI" in d2 and "16,000 characters" in d2
    assert '#scene-status` must become exactly `quality-high' in d3 and "ambient" in d3 and "clearly visible" in d3 and "14,000 characters" in d3
    assert "rebuild a concise complete document" in (root/"repair.txt").read_text()
