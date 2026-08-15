from pathlib import Path
import hashlib
import html
import json

SECTIONS = ("overview", "speed", "context", "artifacts", "qa", "editorial", "evidence", "recommendations", "failures")


def generate_report(results_path: Path, out_dir: Path) -> Path:
    results_path = Path(results_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.loads(results_path.read_text())
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True).replace("</script", "<\\/script")
    failures = html.escape(json.dumps(data.get("failures", []), ensure_ascii=False, indent=2))
    speed = data.get("speed", {}).get("decode_tps", {}).get("p50")
    speed_text = "Unavailable" if speed is None else str(speed)
    nav = "".join(f'<a href="#{section}">{section.title()}</a>' for section in SECTIONS)
    bodies = []
    for section in SECTIONS:
        if section == "overview":
            body = (
                f'<h2>Run {html.escape(data.get("run_id", ""))}</h2>'
                f'<div class="state {data.get("state", "").lower()}">{html.escape(data.get("state", ""))}</div>'
                f'<p>Model: {html.escape(str(data.get("model", {}).get("id", "Unavailable")))}</p>'
            )
        elif section == "speed":
            body = f'<h2>Speed</h2><div class="metric"><strong>{speed_text}</strong><span>decode tok/s p50</span></div>'
        elif section == "failures":
            body = f'<h2>Failures</h2><pre>{failures}</pre>'
        else:
            body = f'<h2>{section.title()}</h2><pre>{html.escape(json.dumps(data.get(section, {}), ensure_ascii=False, indent=2))}</pre>'
        bodies.append(f'<section id="{section}">{body}</section>')
    doc = f'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FJSON Local Benchmark</title><style>
:root{{--bg:#061018;--card:#0e2030;--text:#f7f7ff;--muted:#90a7b8;--a:#259bb5;--ok:#38d996;--bad:#ff6577}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 20% 0,#10354a,var(--bg) 45%);color:var(--text);font:16px system-ui;display:grid;grid-template-columns:230px 1fr;min-height:100vh}}
nav{{padding:28px;position:sticky;top:0;height:100vh;border-right:1px solid #274054}}nav:before{{content:'FJSON / BENCH';display:block;color:var(--a);font-weight:900;margin-bottom:24px}}nav a{{display:block;color:var(--muted);text-decoration:none;padding:9px 0}}nav a:hover{{color:white}}
main{{padding:32px;max-width:1200px}}section{{background:linear-gradient(145deg,#102536,#091722);border:1px solid #274054;border-radius:18px;padding:24px;margin-bottom:20px;box-shadow:0 12px 36px #0006}}h2{{margin-top:0}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;color:#b8d0df}}.state{{display:inline-block;padding:8px 14px;border-radius:999px;background:#24384a}}.state.pass{{background:#0b513a;color:#b7ffe2}}.state.fail{{background:#5a1d2a;color:#ffd2da}}.metric strong{{font-size:48px;color:var(--a);display:block}}.metric span{{color:var(--muted)}}
@media(max-width:768px){{body{{display:block}}nav{{position:static;height:auto;display:flex;gap:16px;overflow:auto;border-right:0;border-bottom:1px solid #274054}}nav:before{{display:none}}nav a{{white-space:nowrap}}main{{padding:18px}}}}
</style></head><body><nav>{nav}</nav><main>{''.join(bodies)}</main><script id="benchmark-data" type="application/json">{raw}</script><script>const d=JSON.parse(document.querySelector('#benchmark-data').textContent);document.documentElement.dataset.state=d.state;</script></body></html>'''
    target = out_dir / "index.html"
    target.write_text(doc)
    manifest = {
        "results_sha256": hashlib.sha256(results_path.read_bytes()).hexdigest(),
        "report_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return target
