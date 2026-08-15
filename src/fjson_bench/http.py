from dataclasses import dataclass
import json
from urllib.request import Request,urlopen
from urllib.error import HTTPError
@dataclass(frozen=True)
class HttpResponse: status:int; headers:dict[str,str]; data:dict
class HttpFailure(RuntimeError):
    def __init__(self,status,body): super().__init__(f"HTTP {status}"); self.status=status; self.body=body
def request_json(url,*,method="GET",headers=None,payload=None,timeout_s=30,max_bytes=8388608):
    data=None if payload is None else json.dumps(payload).encode()
    req=Request(url,data=data,headers=headers or {},method=method)
    try:
        with urlopen(req,timeout=timeout_s) as resp:
            raw=resp.read(max_bytes+1); status=resp.status; hs={k.lower():v for k,v in resp.headers.items()}
    except HTTPError as e:
        body=e.read(max_bytes).decode("utf-8","replace"); raise HttpFailure(e.code,body) from e
    if len(raw)>max_bytes: raise ValueError("response exceeds max_bytes")
    obj=json.loads(raw.decode("utf-8"))
    if not isinstance(obj,dict): raise ValueError("response must be a JSON object")
    return HttpResponse(status,hs,obj)
