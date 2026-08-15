import json
import pytest
from fjson_bench.contracts import RunState
from fjson_bench.ledger import RunLedger

def test_ledger_appends_transitions(tmp_path):
    ledger = RunLedger.create(tmp_path / "run-a", "run-a")
    ledger.transition(RunState.PREFLIGHT, {"health": "ok"})
    ledger.transition(RunState.RUNNING)
    rows = [json.loads(x) for x in (tmp_path / "run-a/events.jsonl").read_text().splitlines()]
    assert [r["state"] for r in rows] == ["PENDING", "PREFLIGHT", "RUNNING"]

def test_final_state_is_immutable(tmp_path):
    ledger = RunLedger.create(tmp_path / "run-b", "run-b")
    ledger.transition(RunState.FAIL, {"reason": "timeout"})
    with pytest.raises(ValueError, match="final"):
        ledger.transition(RunState.PASS)
