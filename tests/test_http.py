import json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import pytest
from fjson_bench.http import HttpFailure, request_json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, body = (500, b'{"error":"fixture failure"}') if self.path == "/fail" else (200, b'[1]') if self.path == "/array" else (200, b'{"status":"ok"}')
        self.send_response(status); self.send_header("Content-Type","application/json"); self.end_headers(); self.wfile.write(body)
    def log_message(self, *args): pass

@pytest.fixture
def server():
    s=ThreadingHTTPServer(("127.0.0.1",0),Handler); t=threading.Thread(target=s.serve_forever,daemon=True); t.start()
    yield f"http://127.0.0.1:{s.server_port}"
    s.shutdown(); t.join()

def test_request_json_ok(server):
    r=request_json(server+"/ok", method="GET", timeout_s=2)
    assert r.status==200 and r.data=={"status":"ok"}

def test_request_json_preserves_500(server):
    with pytest.raises(HttpFailure) as e: request_json(server+"/fail", method="GET", timeout_s=2)
    assert e.value.status==500 and e.value.body=='{"error":"fixture failure"}'

def test_request_json_rejects_array(server):
    with pytest.raises(ValueError, match="JSON object"): request_json(server+"/array", method="GET", timeout_s=2)
