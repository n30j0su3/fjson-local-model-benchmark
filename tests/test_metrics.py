from fjson_bench.metrics import summarize, comparable

def test_summary():
    s=summarize([10.0,20.0,30.0])
    assert s["count"]==3 and s["p50"]==20.0 and s["p95"]==30.0

def test_comparison_rejects_hardware_drift():
    ok,reasons=comparable({"hardware_sha":"a"},{"hardware_sha":"b"})
    assert not ok and reasons==["hardware_sha differs"]
