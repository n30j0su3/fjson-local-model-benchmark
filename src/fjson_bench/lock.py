from pathlib import Path
import json, os, time
class RunLock:
    def __init__(self,path,run_id): self.path=Path(path); self.run_id=run_id; self.start_id=self._start(os.getpid())
    @staticmethod
    def _start(pid):
        try: return Path(f"/proc/{pid}/stat").read_text().split()[21]
        except (OSError,IndexError): return "unknown"
    def acquire(self):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        payload={"pid":os.getpid(),"run_id":self.run_id,"start_id":self.start_id,"created":time.time()}
        try:
            fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        except FileExistsError:
            try: old=json.loads(self.path.read_text())
            except Exception: raise RuntimeError("active run lock is unreadable")
            if Path(f"/proc/{old.get('pid')}").exists() and self._start(old.get('pid'))==old.get('start_id'): raise RuntimeError(f"active run: {old.get('run_id')}")
            self.path.unlink(); return self.acquire()
        with os.fdopen(fd,"w") as h: json.dump(payload,h)
    def release(self):
        old=json.loads(self.path.read_text())
        if old.get("pid")!=os.getpid() or old.get("run_id")!=self.run_id or old.get("start_id")!=self.start_id: raise RuntimeError("lock ownership mismatch")
        self.path.unlink()
