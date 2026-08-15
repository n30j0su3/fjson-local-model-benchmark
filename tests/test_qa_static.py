from pathlib import Path
from fjson_bench.qa_static import run_static_qa

def test_pass_html_is_clean():
    r=run_static_qa(Path("tests/fixtures/html/pass.html"),required_ids=["toggle","state"]); assert r["status"]=="PASS"

def test_external_network_is_blocked():
    r=run_static_qa(Path("tests/fixtures/html/external-network.html")); assert "NETWORK_EXTERNAL" in [x["code"] for x in r["failures"]]

def test_bad_js_is_detected():
    r=run_static_qa(Path("tests/fixtures/html/bad-js.html")); assert "JS_SYNTAX" in [x["code"] for x in r["failures"]]

def test_missing_ids_are_individual():
    r=run_static_qa(Path("tests/fixtures/html/pass.html"),required_ids=["missing-a","missing-b"]); assert [x["id"] for x in r["failures"]]==["missing-a","missing-b"]
