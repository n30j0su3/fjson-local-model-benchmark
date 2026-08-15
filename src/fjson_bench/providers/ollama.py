import time
from fjson_bench.http import request_json
from .base import ChatResult

class OllamaProvider:
    def __init__(self,endpoint,model,timeout_s=600): self.endpoint=endpoint.rstrip("/"); self.model=model; self.timeout_s=timeout_s
    def health(self):
        data=request_json(self.endpoint+"/api/tags",method="GET",timeout_s=min(10,self.timeout_s)).data
        return {"status":"ok","models":data.get("models",[])}
    def model_identity(self):
        return {"id":self.model,"backend":"ollama"}
    def chat(self,messages,*,max_tokens,temperature=0.0):
        started=time.monotonic()
        data=request_json(self.endpoint+"/api/chat",method="POST",headers={"Content-Type":"application/json"},payload={"model":self.model,"messages":messages,"stream":False,"options":{"num_predict":max_tokens,"temperature":temperature}},timeout_s=self.timeout_s).data
        pcount=data.get("prompt_eval_count"); pdur=data.get("prompt_eval_duration"); dcount=data.get("eval_count"); ddur=data.get("eval_duration"); native={}
        if pcount is not None and pdur: native["prompt_per_second"]=pcount/(pdur/1e9)
        if dcount is not None and ddur: native["predicted_per_second"]=dcount/(ddur/1e9)
        for key in ("load_duration","total_duration"):
            if isinstance(data.get(key),(int,float)): native[key+"_seconds"]=data[key]/1e9
        return ChatResult(data["message"]["content"],pcount,dcount,time.monotonic()-started,native,data)
