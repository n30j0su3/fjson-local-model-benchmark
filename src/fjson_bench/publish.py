from pathlib import Path
import hashlib,ipaddress,json,re
class PublicationBlocked(RuntimeError): pass
ALLOWED_FILES={"results.json","manifest.json","receipt.json"}
SECRET_PATTERNS=[re.compile(r"Bearer\s+[A-Za-z0-9._-]{20,}"),re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),re.compile(r"/home/[^/\s]+/")]
IP_RE=re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
def _allowed(rel):
    if str(rel) in ALLOWED_FILES: return True
    if rel.parts[0] in {"report","editorial"}: return True
    if rel.parts[0] == "qa": return len(rel.parts) > 1 and rel.parts[1] in {"screenshots","charts"}
    if rel.parts[0] == "deliverables":
        return len(rel.parts) > 2 and rel.parts[2] in {"packaged","repaired","repaired-packaged","qa"}
    return False
def _public_bytes(path,rel):
    data=path.read_bytes()
    rel_text=rel.as_posix()
    if rel_text=="receipt.json":
        payload=json.loads(data)
        payload["run_root"]="."
        payload["report"]="report/index.html"
        return (json.dumps(payload,indent=2,sort_keys=True)+"\n").encode()
    if len(rel.parts)>=4 and rel.parts[0]=="deliverables" and rel.parts[-2:]==("qa","index.json"):
        payload=json.loads(data)
        for viewport in payload.get("browser",{}).get("viewports",[]):
            screenshot=viewport.get("screenshot")
            if screenshot: viewport["screenshot"]="index/"+Path(screenshot).name
        return (json.dumps(payload,indent=2,sort_keys=True)+"\n").encode()
    return data
def _scan(path,rel,data=None):
    if path.is_symlink(): raise PublicationBlocked(f"symlink blocked: {rel}")
    data=path.read_bytes() if data is None else data
    if len(data)>25*1024*1024: raise PublicationBlocked(f"oversize blocked: {rel}")
    text=data.decode("utf-8","ignore")
    if any(p.search(text) for p in SECRET_PATTERNS): raise PublicationBlocked(f"secret category blocked: {rel}")
    for token in IP_RE.findall(text):
        try:
            if ipaddress.ip_address(token).is_private: raise PublicationBlocked(f"private topology blocked: {rel}")
        except ValueError: pass
    return hashlib.sha256(data).hexdigest()
def build_public_pack(run_root,destination,dry_run=True,approval=None):
    root=Path(run_root).resolve(); dest=Path(destination); rows=[]; public_bytes={}
    try:
        run_state=json.loads((root/"results.json").read_text()).get("state")
    except (OSError,json.JSONDecodeError):
        run_state=None
    if run_state!="PASS": raise PublicationBlocked("only PASS runs can be published")
    source_manifest=root/"manifest.json"
    if not source_manifest.exists(): raise PublicationBlocked("source manifest required")
    source_manifest_sha256=None
    if source_manifest.exists():
        if source_manifest.is_symlink() or not source_manifest.resolve().is_relative_to(root):
            raise PublicationBlocked("source manifest path blocked")
        source_manifest_sha256=hashlib.sha256(source_manifest.read_bytes()).hexdigest()
    for path in sorted(root.rglob("*")):
        if path.is_dir(): continue
        rel=path.relative_to(root)
        if not _allowed(rel): continue
        if str(rel)=="manifest.json": continue
        if path.is_symlink():
            raise PublicationBlocked(f"symlink blocked: {rel}")
        if path.resolve().is_relative_to(root) is False:
            raise PublicationBlocked(f"path escape blocked: {rel}")
        data=_public_bytes(path,rel)
        rows.append({"path":str(rel),"sha256":_scan(path,rel,data),"bytes":len(data)})
        public_bytes[str(rel)]=data
    if not rows: raise PublicationBlocked("public pack is empty")
    public_manifest={"version":1,"source_manifest_sha256":source_manifest_sha256,"files":{row["path"]:row["sha256"] for row in rows}}
    manifest_data=json.dumps(public_manifest,indent=2,sort_keys=True).encode()
    rows.append({"path":"manifest.json","sha256":hashlib.sha256(manifest_data).hexdigest(),"bytes":len(manifest_data)})
    rows.sort(key=lambda row: row["path"])
    approval_request={"required_approver":"N30","exact_action":"publish_pack","manifest_fingerprint":source_manifest_sha256}
    if not dry_run:
        if not isinstance(approval,dict) or approval.get("approved_by")!="N30" or approval.get("exact_action")!="publish_pack":
            raise PublicationBlocked("N30 approval required for publish_pack")
        if approval.get("manifest_fingerprint")!=source_manifest_sha256:
            raise PublicationBlocked("approval manifest fingerprint mismatch")
        if dest.exists(): raise PublicationBlocked("destination already exists")
        for row in rows:
            if row["path"]=="manifest.json": continue
            target=dest/row["path"]; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(public_bytes[row["path"]])
        (dest/"manifest.json").write_bytes(manifest_data)
    return {"status":"DRY_RUN_PASS" if dry_run else "PACKAGED","source":str(root),"destination":str(dest),"files":rows,"approval_request":approval_request}
