from pathlib import Path
from fjson_bench.providers.base import ChatResult
from fjson_bench.artifact_runner import run_artifact

GOOD='<!doctype html><html><body><button id="toggle">go</button><div id="state">ready</div><script>document.querySelector("#toggle").onclick=()=>document.querySelector("#state").textContent="changed"</script></body></html>'
class SeqProvider:
    def __init__(self,values): self.values=list(values); self.calls=[]
    def chat(self,messages,**kwargs):
        self.calls.append(messages[-1]["content"]); text=self.values.pop(0); return ChatResult(text,1,1,.1,{}, {"text":text})

def test_valid_artifact_needs_no_repair(tmp_path):
    p=SeqProvider(["plan",GOOD]); out=run_artifact(p,"demo","PLAN","BUILD","REPAIR",tmp_path,["toggle","state"],[{"selector":"#toggle","expect":"#state","value":"changed"}])
    assert out.final_status=="PASS" and out.repair_attempts==0 and Path(out.strict_path).exists()
    assert len(p.calls)==2

def test_invalid_artifact_gets_one_repair(tmp_path):
    p=SeqProvider(["plan","<html><body>broken</body></html>",GOOD]); out=run_artifact(p,"demo","PLAN","BUILD","REPAIR",tmp_path,["toggle","state"],[{"selector":"#toggle","expect":"#state","value":"changed"}])
    assert out.final_status=="PASS" and out.repair_attempts==1 and Path(out.repaired_path).exists()
    assert len(p.calls)==3 and "FAILURES::" in p.calls[-1]
    assert "<html><body>broken" in p.calls[-1]
    assert "BUILD_CONTRACT::\nBUILD" in p.calls[-1]

def test_browser_failures_are_included_in_repair_prompt(tmp_path):
    broken='<!doctype html><html><body><button id="toggle">go</button><div id="state">ready</div></body></html>'
    p=SeqProvider(["plan",broken,GOOD])
    out=run_artifact(p,"demo","PLAN","BUILD","REPAIR",tmp_path,["toggle","state"],[{"selector":"#toggle","expect":"#state","value":"changed"}])
    assert out.final_status=="PASS"
    assert "INTERACTION" in p.calls[-1]
