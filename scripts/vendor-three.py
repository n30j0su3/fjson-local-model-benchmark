#!/usr/bin/env python3
import hashlib, io, json, tarfile, urllib.request
from pathlib import Path
URL="https://registry.npmjs.org/three/-/three-0.160.0.tgz"
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/"vendor/three"
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(URL,timeout=60) as r: payload=r.read(20_000_000)
    wanted={"package/build/three.min.js":"three.min.js","package/LICENSE":"LICENSE"}
    with tarfile.open(fileobj=io.BytesIO(payload),mode="r:gz") as tf:
        for member,dest in wanted.items():
            info=tf.getmember(member)
            if not info.isfile() or ".." in Path(info.name).parts: raise RuntimeError("unsafe tar member")
            data=tf.extractfile(info).read(); (OUT/dest).write_bytes(data)
    files={p:hashlib.sha256((OUT/p).read_bytes()).hexdigest() for p in wanted.values()}
    manifest={"package":"three","version":"0.160.0","license":"MIT","source":URL,"files":files}
    (OUT/"MANIFEST.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    print(json.dumps(manifest,sort_keys=True))
if __name__=="__main__": main()
