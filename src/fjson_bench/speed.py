import json
from .metrics import summarize
def run_speed(provider,preset,evidence_dir):
    evidence_dir.mkdir(parents=True,exist_ok=True); reps=[]
    for i in range(preset["repetitions"]):
        r=provider.chat([{"role":"user","content":preset["speed_prompt"]}],max_tokens=preset["max_output_tokens"])
        (evidence_dir/f"raw-{i+1}.json").write_text(json.dumps(r.raw,sort_keys=True))
        tps=r.native_timings.get("predicted_per_second")
        provenance="native"
        if tps is None and r.decode_tokens and r.wall_seconds: tps=r.decode_tokens/r.wall_seconds; provenance="estimated"
        reps.append({"repetition":i+1,"decode_tps":tps,"provenance":provenance})
    vals=[x["decode_tps"] for x in reps if x["decode_tps"] is not None]
    return {"repetitions":reps,"summary":{"decode_tps":summarize(vals)}}
