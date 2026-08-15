import json
from pathlib import Path
from .base import ChatResult
class FakeProvider:
    def __init__(self,data): self.data=data; self.calls=[]
    @classmethod
    def from_file(cls,path): return cls(json.loads(Path(path).read_text()))
    def health(self): return {"status":"ok","provider":"fake"}
    def model_identity(self): return {"id":"fake","backend":"fixture"}
    def chat(self,messages,*,max_tokens,temperature=0.0):
        key=messages[-1]["content"]; self.calls.append(key); x=self.data[key]
        return ChatResult(x["text"],x.get("prompt_tokens"),x.get("decode_tokens"),x.get("wall_seconds",0.0),x.get("native_timings",{}),x)
