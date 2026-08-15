import hashlib,json
from pathlib import Path
MARKER='<script src="./vendor/three.min.js"></script>'
class ThreePackError(ValueError): pass
def verify_vendor(root):
    root=Path(root); m=json.loads((root/"MANIFEST.json").read_text())
    return all(hashlib.sha256((root/n).read_bytes()).hexdigest()==sha for n,sha in m["files"].items())
def inline_three(source,vendor_root,destination):
    source=Path(source); vendor_root=Path(vendor_root); destination=Path(destination)
    if not verify_vendor(vendor_root): raise ThreePackError("vendor hash mismatch")
    text=source.read_text(); count=text.count(MARKER)
    if count!=1: raise ThreePackError("expected exactly one Three.js marker")
    js=(vendor_root/"three.min.js").read_text(); sha=hashlib.sha256(js.encode()).hexdigest()
    text=text.replace(MARKER,f'<script>/* THREE_VENDOR_SHA256={sha} */\n{js}\n</script>')
    destination.parent.mkdir(parents=True,exist_ok=True); destination.write_text(text); return destination
