from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import ipaddress
import json
import os
import re
from typing import cast
from .run import PROJECT_ROOT, execute_run

SAFE = re.compile(r"^[A-Za-z0-9._:/-]{1,120}$")
PRESETS = {"speed", "quality", "full-editorial"}
FIELDS = {"config", "preset", "provider", "model"}


class RequestBlocked(ValueError):
    pass


class BridgeServer(ThreadingHTTPServer):
    allowed_cidr: str
    config_dir: Path


def source_allowed(address, cidr):
    try:
        source = ipaddress.ip_address(address)
        return source.is_loopback or source in ipaddress.ip_network(cidr, strict=True)
    except ValueError:
        return False


def validate_payload(payload):
    if not isinstance(payload, dict) or not {"config", "preset"} <= set(payload) or set(payload) - FIELDS:
        raise RequestBlocked("invalid payload fields")
    if payload["preset"] not in PRESETS:
        raise RequestBlocked("invalid preset")
    for field in ("config", "provider", "model"):
        value = payload.get(field)
        if value is not None and (not isinstance(value, str) or not SAFE.fullmatch(value)):
            raise RequestBlocked(f"invalid {field}")
    if "/" in payload["config"] or ":" in payload["config"]:
        raise RequestBlocked("invalid config")
    return dict(payload)


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "FJSONBenchBridge/0.1"

    def _json(self, status, payload):
        body = json.dumps(payload, sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _allowed(self):
        server = cast(BridgeServer, self.server)
        return source_allowed(self.client_address[0], server.allowed_cidr)

    def do_GET(self):
        if self.path != "/health":
            return self._json(404, {"status": "not_found"})
        if not self._allowed():
            return self._json(403, {"status": "blocked"})
        return self._json(200, {"status": "ok", "service": "fjson-benchmark-bridge"})

    def do_POST(self):
        if self.path != "/run":
            return self._json(404, {"status": "not_found"})
        if not self._allowed():
            return self._json(403, {"status": "blocked"})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 8192:
                raise RequestBlocked("invalid body size")
            payload = validate_payload(json.loads(self.rfile.read(length)))
            server = cast(BridgeServer, self.server)
            config = (server.config_dir / f"{payload['config']}.json").resolve()
            if config.parent != server.config_dir.resolve() or not config.is_file():
                raise RequestBlocked("unknown config")
            receipt = execute_run(config, payload["preset"], payload.get("provider"), payload.get("model"))
            return self._json(200 if receipt["status"] == "PASS" else 500, receipt)
        except (RequestBlocked, json.JSONDecodeError) as error:
            return self._json(422, {"status": "blocked", "error": str(error)})
        except Exception as error:
            return self._json(500, {"status": "error", "error": type(error).__name__})

    def log_message(self, format, *args):
        return


def serve():
    bind = os.environ.get("FJSON_BENCH_BIND", "127.0.0.1")
    port = int(os.environ.get("FJSON_BENCH_PORT", "9163"))
    server = BridgeServer((bind, port), BridgeHandler)
    server.allowed_cidr = os.environ.get("FJSON_BENCH_ALLOWED_CIDR", "127.0.0.1/32")
    server.config_dir = Path(os.environ.get("FJSON_BENCH_CONFIG_DIR", PROJECT_ROOT / "config/local"))
    server.serve_forever()


if __name__ == "__main__":
    serve()
