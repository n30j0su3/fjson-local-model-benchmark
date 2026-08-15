from html.parser import HTMLParser
from pathlib import Path
import re,subprocess,tempfile
class Collector(HTMLParser):
    def __init__(self): super().__init__(); self.ids=set(); self.urls=[]; self.scripts=[]; self._script=False; self._buf=[]
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if "id" in d: self.ids.add(d["id"])
        for k in ("src","href","action"):
            if d.get(k): self.urls.append(d[k])
        if tag=="script" and not d.get("src"): self._script=True; self._buf=[]
    def handle_data(self,data):
        if self._script: self._buf.append(data)
    def handle_endtag(self,tag):
        if tag=="script" and self._script: self.scripts.append("".join(self._buf)); self._script=False
def run_static_qa(path,required_ids=None):
    text=Path(path).read_text(); c=Collector(); failures=[]
    try: c.feed(text)
    except Exception as e: failures.append({"code":"HTML_PARSE","detail":str(e)})
    for rid in required_ids or []:
        if rid not in c.ids: failures.append({"code":"MISSING_ID","id":rid})
    external=[u for u in c.urls if re.match(r"(?i)https?://",u)]
    external += re.findall(r'''(?i)(?:fetch|WebSocket|EventSource|import)\s*\(\s*['"]https?://''', text)
    if external: failures.append({"code":"NETWORK_EXTERNAL","count":len(external)})
    for script in c.scripts:
        if not script.strip() or script.lstrip().startswith('{'): continue
        with tempfile.NamedTemporaryFile("w",suffix=".js",delete=False) as h: h.write(script); name=h.name
        try:
            p=subprocess.run(["node","--check",name],capture_output=True,text=True,timeout=10)
            if p.returncode: failures.append({"code":"JS_SYNTAX","detail":p.stderr[-1000:]})
        finally: Path(name).unlink(missing_ok=True)
    return {"status":"PASS" if not failures else "FAIL","failures":failures,"ids":sorted(c.ids)}
