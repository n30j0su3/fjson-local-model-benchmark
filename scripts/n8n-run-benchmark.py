#!/usr/bin/env python3
import argparse,json,re,subprocess
from pathlib import Path
SAFE=re.compile(r"^[a-zA-Z0-9._:/-]{1,120}$")
def checked(value,field):
    if not SAFE.fullmatch(value): raise SystemExit(f"invalid {field}")
    return value
def main(argv=None):
    p=argparse.ArgumentParser(); p.add_argument("--config",required=True); p.add_argument("--provider",required=True); p.add_argument("--model",required=True); p.add_argument("--preset",choices=["speed","quality","full-editorial"],required=True); a=p.parse_args(argv)
    root=Path(__file__).resolve().parents[1]; cmd=[str(root/".venv/bin/benchctl"),"run","--config",checked(a.config,"config"),"--provider",checked(a.provider,"provider"),"--model",checked(a.model,"model"),"--preset",a.preset]
    result=subprocess.run(cmd,capture_output=True,text=True,shell=False); print(json.dumps({"status":"PASS" if result.returncode==0 else "FAIL","exit_code":result.returncode,"stdout":result.stdout[-4000:],"stderr":result.stderr[-4000:]})); return result.returncode
if __name__=="__main__": raise SystemExit(main())
