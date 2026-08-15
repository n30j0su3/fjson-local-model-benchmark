from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import math, re

class Provenance(StrEnum):
    NATIVE="native"; DERIVED="derived"; ESTIMATED="estimated"; UNAVAILABLE="unavailable"
class RunState(StrEnum):
    PENDING="PENDING"; PREFLIGHT="PREFLIGHT"; RUNNING="RUNNING"; QA="QA"; REPORTING="REPORTING"; PASS="PASS"; FAIL="FAIL"; INTERRUPTED="INTERRUPTED"

def slugify(value):
    s=re.sub(r"[^a-z0-9]+","-",value.lower()).strip("-")
    if not s: raise ValueError("model must produce a non-empty public slug")
    return s[:80]

@dataclass(frozen=True)
class RunSpec:
    provider:str; model:str; preset:str; repetitions:int=3; endpoint:str|None=None; api_key_env:str|None=None; options:dict=field(default_factory=dict)
    def __post_init__(self):
        if self.preset not in {"speed","quality","full-editorial"}: raise ValueError("preset must be speed, quality, or full-editorial")
        if self.repetitions<1: raise ValueError("repetitions must be at least 1")
    def run_id(self,now=None):
        d=(now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        return f"{d:%Y%m%dT%H%M%SZ}--{slugify(self.model)}--{self.preset}"

@dataclass(frozen=True)
class Metric:
    name:str; value:float|None; unit:str; provenance:Provenance; evidence_path:str; repetition:int|None=None
    def __post_init__(self):
        if self.value is not None and not math.isfinite(self.value): raise ValueError("metric value must be finite")
