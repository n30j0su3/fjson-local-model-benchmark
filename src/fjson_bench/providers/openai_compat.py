import time
from urllib.parse import urlsplit
from fjson_bench.http import request_json, HttpFailure
from .base import ChatResult

class OpenAICompatibleProvider:
    def __init__(self, endpoint, model, api_key=None, timeout_s=600):
        self.endpoint=endpoint.rstrip("/"); self.model=model; self._api_key=api_key; self.timeout_s=timeout_s
        if self.endpoint.endswith("/v1"): self.endpoint=self.endpoint[:-3]
    def __repr__(self): return f"OpenAICompatibleProvider(endpoint={self.endpoint!r}, model={self.model!r})"
    def _headers(self):
        h={"Content-Type":"application/json"}
        if self._api_key: h["Authorization"]=f"Bearer {self._api_key}"
        return h
    def health(self):
        try: return request_json(self.endpoint+"/health",method="GET",timeout_s=min(10,self.timeout_s)).data
        except HttpFailure:
            self.model_identity(); return {"status":"ok","source":"models"}
    def model_identity(self):
        data=request_json(self.endpoint+"/v1/models",method="GET",headers=self._headers(),timeout_s=min(20,self.timeout_s)).data
        return {"id":self.model,"models":data.get("data",[]),"backend":"openai-compatible"}
    def chat(self,messages,*,max_tokens,temperature=0.0):
        started=time.monotonic()
        data=request_json(self.endpoint+"/v1/chat/completions",method="POST",headers=self._headers(),payload={"model":self.model,"messages":messages,"max_tokens":max_tokens,"temperature":temperature,"stream":False},timeout_s=self.timeout_s).data
        usage=data.get("usage",{}); timings=data.get("timings",{})
        return ChatResult(data["choices"][0]["message"]["content"],usage.get("prompt_tokens"),usage.get("completion_tokens"),time.monotonic()-started,{k:float(v) for k,v in timings.items() if isinstance(v,(int,float))},data)
