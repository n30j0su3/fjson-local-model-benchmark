import json, os
import pytest
from fjson_bench.lock import RunLock

def test_second_live_lock_is_rejected(tmp_path):
    first = RunLock(tmp_path / "bench.lock", "run-a")
    first.acquire()
    with pytest.raises(RuntimeError, match="active run"):
        RunLock(tmp_path / "bench.lock", "run-b").acquire()
    first.release()

def test_release_requires_owned_pid(tmp_path):
    lock = RunLock(tmp_path / "bench.lock", "run-a")
    lock.acquire()
    lock.path.write_text(json.dumps({"pid": os.getpid(), "run_id": "other", "start_id": lock.start_id}))
    with pytest.raises(RuntimeError, match="ownership"):
        lock.release()
