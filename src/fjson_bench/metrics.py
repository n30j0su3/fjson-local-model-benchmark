import math, statistics
def summarize(values):
    v=sorted(float(x) for x in values); n=len(v)
    if not n: return {"count":0,"p50":None,"p95":None,"mean":None,"cv":None}
    m=statistics.mean(v); p95=v[max(0,math.ceil(.95*n)-1)]
    return {"count":n,"p50":statistics.median(v),"p95":p95,"mean":m,"cv":statistics.pstdev(v)/m if m else None}
def comparable(a,b):
    keys=("hardware_sha","backend_family","prompt_sha","context_budget","output_budget","repetitions","telemetry_method")
    reasons=[f"{k} differs" for k in keys if a.get(k)!=b.get(k)]
    return not reasons,reasons
