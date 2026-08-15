import json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from fjson_bench.providers.openai_compat import OpenAICompatibleProvider
from fjson_bench.providers.ollama import OllamaProvider

class Handler(BaseHTTPRequestHandler):
    def _json(self, obj):
        body=json.dumps(obj).encode(); self.send_response(200); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=="/health": return self._json({"status":"ok"})
        if self.path=="/v1/models": return self._json({"data":[{"id":"demo"}]})
        if self.path=="/api/tags": return self._json({"models":[{"name":"demo"}]})
        self.send_error(404)
    def do_POST(self):
        n=int(self.headers.get("Content-Length","0")); payload=json.loads(self.rfile.read(n))
        if self.path=="/v1/chat/completions":
            assert self.headers.get("Authorization")=="Bearer secret"
            return self._json({"choices":[{"message":{"content":"OK"}}],"usage":{"prompt_tokens":10,"completion_tokens":2},"timings":{"prompt_per_second":321.5,"predicted_per_second":41.2}})
        if self.path=="/api/chat":
            assert payload["stream"] is False and payload["options"]["num_predict"]==16
            return self._json({"message":{"content":"hello"},"prompt_eval_count":20,"prompt_eval_duration":1000000000,"eval_count":10,"eval_duration":1000000000,"total_duration":2100000000})
        self.send_error(404)
    def log_message(self,*args): pass

@pytest.fixture
def server():
    s=ThreadingHTTPServer(("127.0.0.1",0),Handler); t=threading.Thread(target=s.serve_forever,daemon=True); t.start()
    yield f"http://127.0.0.1:{s.server_port}"
    s.shutdown(); t.join()

def test_openai_adapter_normalizes_response(server):
    p=OpenAICompatibleProvider(server,"demo",api_key="secret")
    assert p.health()["status"]=="ok"
    r=p.chat([{"role":"user","content":"hi"}],max_tokens=16)
    assert (r.text,r.prompt_tokens,r.decode_tokens)==("OK",10,2)
    assert r.native_timings["predicted_per_second"]==41.2
    assert "secret" not in repr(p)

def test_ollama_converts_nanoseconds_to_rates(server):
    p=OllamaProvider(server,"demo")
    assert p.health()["status"]=="ok"
    r=p.chat([{"role":"user","content":"hi"}],max_tokens=16)
    assert r.text=="hello"
    assert r.native_timings["prompt_per_second"]==20.0
    assert r.native_timings["predicted_per_second"]==10.0
