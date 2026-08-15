import json,runpy
from pathlib import Path
import pytest

def test_workflow_is_importable_and_sanitized():
    text=Path("workflows/n8n/miniv-local-model-benchmark.json").read_text(); data=json.loads(text); assert len(data["nodes"])>=6 and data["connections"]
    assert "192"+".168." not in text and "Bea"+"rer " not in text and "api_key" not in text.lower()
    types={node["type"] for node in data["nodes"]}
    assert "n8n-nodes-base.httpRequest" in types
    assert "n8n-nodes-base.executeCommand" not in types
    assert "host.docker.internal:9163/run" in text

def test_wrapper_rejects_shell_metacharacters():
    mod=runpy.run_path("scripts/n8n-run-benchmark.py")
    with pytest.raises(SystemExit,match="invalid model"): mod["checked"]("x;touch /tmp/pwned","model")
