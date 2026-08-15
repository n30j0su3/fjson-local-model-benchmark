from dataclasses import dataclass
from datetime import datetime, timezone
import json, os
from pathlib import Path
from .contracts import RunState
ALLOWED={RunState.PENDING:{RunState.PREFLIGHT,RunState.FAIL,RunState.INTERRUPTED},RunState.PREFLIGHT:{RunState.RUNNING,RunState.FAIL,RunState.INTERRUPTED},RunState.RUNNING:{RunState.QA,RunState.REPORTING,RunState.FAIL,RunState.INTERRUPTED},RunState.QA:{RunState.REPORTING,RunState.FAIL,RunState.INTERRUPTED},RunState.REPORTING:{RunState.PASS,RunState.FAIL,RunState.INTERRUPTED},RunState.PASS:set(),RunState.FAIL:set(),RunState.INTERRUPTED:set()}
@dataclass
class RunLedger:
    root:Path; run_id:str; state:RunState
    @classmethod
    def create(cls,root,run_id):
        root=Path(root); root.mkdir(parents=True,exist_ok=False); x=cls(root,run_id,RunState.PENDING); x._append(RunState.PENDING,{}); return x
    def transition(self,state,detail=None):
        if state not in ALLOWED[self.state]: raise ValueError(f"illegal or final transition: {self.state} -> {state}")
        self._append(state,detail or {}); self.state=state
    def _append(self,state,detail):
        row={"run_id":self.run_id,"state":state.value,"at":datetime.now(timezone.utc).isoformat(),"detail":detail}
        with (self.root/"events.jsonl").open("a",encoding="utf-8") as h:
            h.write(json.dumps(row,sort_keys=True)+"\n"); h.flush(); os.fsync(h.fileno())
