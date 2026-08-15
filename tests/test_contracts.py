from datetime import datetime, timezone
import pytest
from fjson_bench.contracts import Metric, Provenance, RunSpec

def test_metric_rejects_non_finite_value():
    with pytest.raises(ValueError, match="finite"):
        Metric("decode_tps", float("nan"), "tok/s", Provenance.NATIVE, "metrics/raw.json")

def test_run_spec_rejects_unknown_preset():
    with pytest.raises(ValueError, match="preset"):
        RunSpec(provider="fake", model="demo", preset="mega")

def test_run_id_is_utc_and_sanitized():
    spec = RunSpec(provider="fake", model="Model / 7B", preset="speed")
    now = datetime(2026, 8, 15, 17, 30, tzinfo=timezone.utc)
    assert spec.run_id(now) == "20260815T173000Z--model-7b--speed"
