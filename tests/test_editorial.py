import json
import pytest
from fjson_bench.editorial import build_claims, write_editorial_kit

def test_claims_are_evidence_bound(tmp_path):
    results={"run_id":"r1","speed":{"decode_tps":{"p50":42.0,"provenance":"native","evidence_path":"metrics/speed.json"}},"context":{"max_verified":32768,"evidence_path":"metrics/context.json"},"comparison":{"eligible":False}}
    claims=build_claims(results); assert claims and all(set(["claim","metric_path","evidence_path","status"])<=set(c) for c in claims)
    assert not any("faster" in c["claim"].lower() for c in claims)
    paths=write_editorial_kit(tmp_path,results); assert len(paths)==7 and all(p.exists() for p in paths)

def test_unknown_metric_cannot_be_claimed():
    with pytest.raises(ValueError,match="evidence_path"): build_claims({"speed":{"decode_tps":{"p50":42}}})
