import json
from fjson_bench.presets import load_preset
from fjson_bench.providers.fake import FakeProvider
from fjson_bench.speed import run_speed

def test_speed_runs_exact_repetitions(tmp_path):
    preset=load_preset("presets/speed.json")
    p=FakeProvider.from_file("tests/fixtures/fake_responses.json")
    out=run_speed(p,preset,tmp_path)
    assert len(out["repetitions"])==3
    assert out["summary"]["decode_tps"]["p50"]==42.0
    assert len(list(tmp_path.glob("raw-*.json")))==3
