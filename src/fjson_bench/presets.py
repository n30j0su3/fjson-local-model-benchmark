import json
from pathlib import Path
ALLOWED={"name","repetitions","speed_prompt","max_output_tokens","context_ladder_tokens","artifacts","editorial","public_pack_dry_run"}
def load_preset(path):
    x=json.loads(Path(path).read_text()); unknown=set(x)-ALLOWED
    if unknown: raise ValueError(f"unknown preset keys: {sorted(unknown)}")
    if x["name"] not in {"speed","quality","full-editorial"} or int(x["repetitions"])<1: raise ValueError("invalid preset")
    return x
