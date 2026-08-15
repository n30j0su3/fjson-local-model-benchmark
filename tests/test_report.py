import json,re
from pathlib import Path
from fjson_bench.report import generate_report

def test_report_is_offline_and_embeds_results(tmp_path):
    p=generate_report(Path("tests/fixtures/results/pass.json"),tmp_path)
    t=p.read_text(); assert not re.search(r'https?://|<script\s+src|<link\s+href',t,re.I)
    m=re.search(r'<script id="benchmark-data" type="application/json">(.*?)</script>',t,re.S); assert json.loads(m.group(1))["state"]=="PASS"
    assert all(f'id="{x}"' in t for x in ["overview","speed","context","artifacts","qa","editorial","evidence","recommendations","failures"])
    assert "Technical contract status" in t and "Visual publication remains subject to human review" in t

def test_fail_report_keeps_reason(tmp_path):
    p=generate_report(Path("tests/fixtures/results/fail.json"),tmp_path); assert "TIMEOUT" in p.read_text() and "Unavailable" in p.read_text()
