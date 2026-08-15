from pathlib import Path
import hashlib,shutil,subprocess
START="<!-- FJSON_BENCHMARK_EXPORTS_START -->"; END="<!-- FJSON_BENCHMARK_EXPORTS_END -->"
def _hash_tree(root):
    h=hashlib.sha256()
    for p in sorted(Path(root).rglob("*")):
        if p.is_file(): h.update(str(p.relative_to(root)).encode()); h.update(p.read_bytes())
    return h.hexdigest()
def export_pack(pack,gallery,slug,dry_run=True,require_git_clean=True,approval=None):
    pack=Path(pack).resolve(); gallery=Path(gallery).resolve(); dest=gallery/"benchmarks"/slug
    if not (pack/"report/index.html").is_file(): raise RuntimeError("pack report/index.html required")
    pack_sha256=_hash_tree(pack)
    if require_git_clean:
        p=subprocess.run(["git","status","--porcelain"],cwd=gallery,capture_output=True,text=True)
        if p.returncode or p.stdout.strip(): raise RuntimeError("gallery worktree is dirty")
    for name in ("index.html","README.md"):
        text=(gallery/name).read_text()
        if START not in text or END not in text: raise RuntimeError(f"missing stable markers in {name}")
    if dest.exists():
        if _hash_tree(dest)==pack_sha256: return {"status":"ALREADY_PRESENT","destination":str(dest)}
        raise RuntimeError("gallery destination collision")
    approval_request={"required_approver":"N30","exact_action":"gallery_export","pack_sha256":pack_sha256}
    if dry_run: return {"status":"DRY_RUN_PASS","destination":str(dest),"pack_sha256":pack_sha256,"approval_request":approval_request}
    if not isinstance(approval,dict) or approval.get("approved_by")!="N30" or approval.get("exact_action")!="gallery_export":
        raise RuntimeError("N30 approval required for gallery_export")
    if approval.get("pack_sha256")!=pack_sha256:
        raise RuntimeError("approval pack fingerprint mismatch")
    shutil.copytree(pack,dest)
    card=f'\n<a class="benchmark-card" href="benchmarks/{slug}/report/index.html" data-export="{slug}">{slug}</a>\n'
    row=f'\n- [{slug}](benchmarks/{slug}/report/index.html)\n'
    idx=gallery/"index.html"; idx.write_text(idx.read_text().replace(END,card+END))
    readme=gallery/"README.md"; readme.write_text(readme.read_text().replace(END,row+END))
    return {"status":"EXPORTED","destination":str(dest),"pack_sha256":pack_sha256}
