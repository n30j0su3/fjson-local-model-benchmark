from pathlib import Path
import json
def build_claims(results):
    claims=[]
    speed=results.get("speed",{}).get("decode_tps",{})
    if speed.get("p50") is not None:
        if not speed.get("evidence_path"): raise ValueError("speed claim requires evidence_path")
        claims.append({"claim":f"Median decode speed was {speed['p50']} tok/s.","metric_path":"speed.decode_tps.p50","evidence_path":speed["evidence_path"],"status":speed.get("provenance","unavailable")})
    context=results.get("context",{})
    if context.get("max_verified") is not None:
        if not context.get("evidence_path"): raise ValueError("context claim requires evidence_path")
        claims.append({"claim":f"Verified context reached {context['max_verified']} tokens.","metric_path":"context.max_verified","evidence_path":context["evidence_path"],"status":"verified"})
    return claims
def write_editorial_kit(run_root,results):
    root=Path(run_root)/"editorial"; root.mkdir(parents=True,exist_ok=True); claims=build_claims(results); run_id=results.get("run_id","unknown")
    assets=[{"beat":i+1,"asset":c["evidence_path"],"purpose":c["claim"]} for i,c in enumerate(claims)]
    studio=[{"beat":a["beat"],"subject":"local model benchmark evidence","composition":"metric and source side by side","why":a["purpose"]} for a in assets]
    content={"claims.json":json.dumps(claims,indent=2),"walkthrough.md":f"# Walkthrough — {run_id}\n\n"+"\n".join(f"- {c['claim']} Source: `{c['evidence_path']}`" for c in claims),"short.md":"# Short 45–60s\n\nHook: Local AI, measured without smoke.\n\n"+" ".join(c["claim"] for c in claims)+"\n\nCTA: inspect the offline evidence pack.","article-brief.md":f"# Article brief\n\nRun `{run_id}`. Explain methodology, verified metrics, artifact QA and limitations. No unsupported comparisons.","shotlist.json":json.dumps(assets,indent=2),"conclusions.md":"# Conclusions\n\n"+("\n".join(f"- {c['claim']}" for c in claims) or "- No publishable metric claims were available."),"studio-prompts.json":json.dumps(studio,indent=2)}
    paths=[]
    for name in sorted(content): p=root/name; p.write_text(content[name]+"\n"); paths.append(p)
    return paths
