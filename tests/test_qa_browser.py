from pathlib import Path
import pytest
pytest.importorskip("playwright.sync_api")
from fjson_bench.qa_browser import run_browser_qa

def test_interaction_changes_dom_at_three_viewports(tmp_path):
    r=run_browser_qa(Path("tests/fixtures/html/pass.html"),tmp_path,[{"selector":"#toggle","expect":"#state","value":"changed"}])
    assert [x["width"] for x in r["viewports"]]==[1600,768,480]
    assert all(x["interaction_pass"] and not x["horizontal_overflow"] for x in r["viewports"])
    assert r["status"]=="PASS"

def test_select_interaction_chooses_next_option_at_three_viewports(tmp_path):
    html=tmp_path/"select.html"
    html.write_text('''<!doctype html><html><body>
<select id="store"><option value="all">All</option><option value="north">North</option></select>
<div id="state">ready</div><script>
document.querySelector("#store").addEventListener("change",()=>document.querySelector("#state").textContent="filtered")
</script></body></html>''')
    receipt=run_browser_qa(html,tmp_path/"select-qa",[{"selector":"#store","expect":"#state","value":"filtered"}])
    assert receipt["status"]=="PASS"
    assert all(x["interaction_pass"] for x in receipt["viewports"])


def test_blocked_network_attempt_is_failure(tmp_path):
    html=tmp_path/"net.html"
    html.write_text('<!doctype html><html><body><img src="https://example.invalid/pixel.png"></body></html>')
    receipt=run_browser_qa(html,tmp_path/"net-qa",[])
    assert receipt["status"]=="FAIL"
    assert receipt["blocked_requests"]
