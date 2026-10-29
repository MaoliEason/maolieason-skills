#!/usr/bin/env python3
"""Render front/side/top orthographic views from one locked Blender scene."""
import argparse,hashlib,json,shutil,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
VIEWS=("front","side","top")
class AdapterError(Exception): pass
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def safe(root,raw):
 if not isinstance(raw,str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts: raise AdapterError("unsafe relative path")
 p=(root/raw).resolve()
 if not p.is_relative_to(root.resolve()): raise AdapterError("path escapes task root")
 return p
def validate(mp):
 mp=Path(mp).resolve(); root=mp.parent; m=json.loads(mp.read_text())
 if m.get("schema_version")!=1 or m.get("task_type")!="orthographic_views" or m.get("operation")!="render_front_side_top": raise AdapterError("invalid orthographic render manifest")
 e=m.get("inputs",{}).get("scene",{})
 if not isinstance(e,dict) or not e.get("path") or not e.get("sha256"): raise AdapterError("inputs.scene path and sha256 required")
 scene=safe(root,e["path"])
 if not scene.is_file() or scene.suffix.lower()!=".blend": raise AdapterError("scene must be an existing .blend file")
 sh=sha(scene)
 if sh!=e["sha256"]: raise AdapterError("scene SHA-256 mismatch")
 cfg=m.get("render",{}); cams=cfg.get("cameras",{})
 if any(not isinstance(cams.get(v),str) or not cams[v] for v in VIEWS): raise AdapterError("front, side, and top camera names required")
 res=cfg.get("resolution")
 if not isinstance(res,list) or len(res)!=2 or any(type(x)!=int or x<64 or x>8192 for x in res): raise AdapterError("resolution must be integer [width,height] from 64 to 8192")
 outs={}; output=m.get("outputs",{})
 for v in VIEWS:
  it=output.get(v,{})
  if not isinstance(it,dict) or not it.get("path"): raise AdapterError("outputs."+v+".path required")
  p=safe(root,it["path"])
  if p.suffix.lower()!=".png" or p.exists(): raise AdapterError("outputs must be new .png files")
  outs[v]=p
 if len(set(map(str,outs.values())))!=3: raise AdapterError("outputs must be distinct")
 rp=safe(root,m.get("receipt","work/blender_receipt.json"))
 if rp.exists(): raise AdapterError("refusing to overwrite receipt")
 blender=m.get("blender_executable","blender")
 if Path(blender).is_absolute():
  if not Path(blender).is_file(): raise AdapterError("Blender executable not found")
 elif shutil.which(blender) is None: raise AdapterError("Blender is not installed or not on PATH")
 return mp,root,m,scene,sh,outs,rp,blender
def run(manifest):
 mp,root,m,scene,sh,outs,rp,blender=validate(manifest)
 helper=Path(__file__).with_name("blender_render_orthographic.py")
 cmd=[blender,"--background",str(scene),"--python",str(helper),"--","--manifest",str(mp)]
 p=subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=900)
 if p.returncode: raise AdapterError("Blender render failed: "+p.stderr[-2000:])
 if any(not x.is_file() or x.stat().st_size<100 for x in outs.values()): raise AdapterError("one or more renders missing or unexpectedly small")
 rec={"schema_version":1,"status":"CANDIDATE_CREATED","adapter":"blender-orthographic-render/1.0.0","task_id":m.get("task_id","unnamed"),"scene_sha256":sh,"cameras":m["render"]["cameras"],"resolution":m["render"]["resolution"],"outputs":{v:{"path":m["outputs"][v]["path"],"sha256":sha(p),"size_bytes":p.stat().st_size} for v,p in outs.items()},"created_at_utc":datetime.now(timezone.utc).isoformat(),"release_status":"NOT_RELEASED_REQUIRES_REVIEW"}
 rp.parent.mkdir(parents=True,exist_ok=True); rp.write_text(json.dumps(rec,indent=2)+"\n")
 return rec,rp
def verify(receipt):
 rp=Path(receipt).resolve(); r=json.loads(rp.read_text())
 if r.get("adapter")!="blender-orthographic-render/1.0.0" or r.get("release_status")!="NOT_RELEASED_REQUIRES_REVIEW": raise AdapterError("invalid receipt")
 root=rp.parent.parent if rp.parent.name=="work" else rp.parent; out={}
 for v in VIEWS:
  x=r.get("outputs",{}).get(v,{})
  p=safe(root,x.get("path"))
  if not p.is_file() or sha(p)!=x.get("sha256"): raise AdapterError(v+" render missing/hash mismatch")
  out[v]=x["sha256"]
 return {"status":"RECEIPT_VERIFIED","scene_sha256":r["scene_sha256"],"outputs_sha256":out}
def main():
 ap=argparse.ArgumentParser(); s=ap.add_subparsers(dest="cmd",required=True)
 a=s.add_parser("run"); a.add_argument("--manifest",required=True)
 b=s.add_parser("verify"); b.add_argument("--receipt",required=True)
 x=ap.parse_args()
 try:
  if x.cmd=="run":
   r,p=run(x.manifest); print(json.dumps({"status":r["status"],"receipt":str(p),"outputs":r["outputs"],"release_status":r["release_status"],"note":"Human review required; not final."},indent=2))
  else: print(json.dumps(verify(x.receipt),indent=2))
  return 0
 except Exception as e: print(json.dumps({"status":"BLOCKED","error":str(e)},indent=2),file=sys.stderr); return 2
if __name__=="__main__": sys.exit(main())
