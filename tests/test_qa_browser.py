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


def test_minimum_mean_luminance_blocks_nearly_black_artifact(tmp_path):
    html=tmp_path/"dark.html"
    html.write_text('<!doctype html><html><style>html,body{margin:0;background:#000;color:#000}</style><body><button id="toggle">x</button><div id="state">ready</div><script>toggle.onclick=()=>state.textContent="changed"</script></body></html>')
    receipt=run_browser_qa(html,tmp_path/"dark-qa",[{"selector":"#toggle","expect":"#state","value":"changed"}],min_mean_luminance=6.0)
    assert receipt["status"]=="FAIL"
    assert all(not x["visual_pass"] for x in receipt["viewports"])
    assert all(any(f["code"]=="LOW_MEAN_LUMINANCE" for f in x["failures"]) for x in receipt["viewports"])


def test_blocked_network_attempt_is_failure(tmp_path):
    html=tmp_path/"net.html"
    html.write_text('<!doctype html><html><body><img src="https://example.invalid/pixel.png"></body></html>')
    receipt=run_browser_qa(html,tmp_path/"net-qa",[])
    assert receipt["status"]=="FAIL"
    assert receipt["blocked_requests"]


def test_scroll_reveal_elements_are_activated_before_full_page_screenshot(tmp_path):
    html=tmp_path/"reveal.html"
    blocks="".join(f'<div class="reveal">block-{i}</div><div class="spacer"></div>' for i in range(8))
    html.write_text(f'''<!doctype html><html><style>
    html{{scroll-behavior:smooth}}body{{margin:0}}.spacer{{height:420px}}.reveal{{height:70px;opacity:0}}.reveal.in{{opacity:1}}
    </style><body>{blocks}
    <script>const io=new IntersectionObserver(es=>es.forEach(e=>{{if(e.isIntersecting)e.target.classList.add('in')}}),{{threshold:.15}});document.querySelectorAll('.reveal').forEach(x=>io.observe(x))</script>
    </body></html>''')
    receipt=run_browser_qa(html,tmp_path/"reveal-qa",[])
    assert receipt["status"]=="PASS"
    assert all(row["reveal_total"]==8 and row["reveal_visible"]==8 for row in receipt["viewports"])
