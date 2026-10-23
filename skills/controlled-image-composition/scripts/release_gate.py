#!/usr/bin/env python3
"""Fail-closed candidate validation and human-approved release gate."""
import argparse, hashlib, json, math, shutil, sys
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageChops

REQUIRED=("base_image","source_module","adapted_module","editable_mask","candidate_image","review_evidence")
STRUCTURE=("platform_edge_aligned","wall_joint_aligned","stair_top_connected","stair_bottom_connected","upper_exit_clear","railing_does_not_block_exit")
class GateError(Exception): pass

def digest(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()

def entry(root,item,label):
 if not isinstance(item,dict): raise GateError(f"{label}: missing path/hash")
 raw=item.get("path","")
 if not isinstance(raw,str) or not raw or Path(raw).is_absolute() or ".." in Path(raw).parts: raise GateError(f"{label}: unsafe relative path")
 p=(root/raw).resolve()
 if not p.is_relative_to(root.resolve()) or not p.is_file(): raise GateError(f"{label}: file missing or outside manifest root")
 actual=digest(p)
 if item.get("sha256")!=actual: raise GateError(f"{label}: SHA-256 mismatch")
 return p,actual

def img(p,label):
 try:
  with Image.open(p) as im: im.load(); return im.convert("RGB")
 except Exception as e: raise GateError(f"{label}: unreadable image: {e}") from e

def anchor_metrics(items,label,n):
 if not isinstance(items,list) or len(items)<n: raise GateError(f"{label}: requires at least {n} independent anchors")
 errors=[]
 for a in items:
  try:
   x,y=map(float,a["expected_px"]); u,v=map(float,a["actual_px"])
   if not all(map(math.isfinite,(x,y,u,v))): raise ValueError()
   errors.append(math.hypot(x-u,y-v))
  except Exception as e: raise GateError(f"{label}: invalid anchor {a!r}") from e
 return {"count":len(errors),"rms_px":round(math.sqrt(sum(e*e for e in errors)/len(errors)),4),"max_error_px":round(max(errors),4)}

def validate(mp):
 mp=Path(mp).resolve(); root=mp.parent
 try: m=json.loads(mp.read_text(encoding="utf-8"))
 except Exception as e: raise GateError(f"invalid manifest: {e}") from e
 if m.get("schema_version")!=1: raise GateError("schema_version must be 1")
 paths={}; hashes={}
 for k in REQUIRED: paths[k],hashes[k]=entry(root,m.get("inputs",{}).get(k),"inputs."+k)
 base,candidate=img(paths["base_image"],"base_image"),img(paths["candidate_image"],"candidate_image")
 if base.size!=candidate.size: raise GateError("candidate dimensions differ from baseline")
 try:
  with Image.open(paths["editable_mask"]) as im: im.load(); mask=im.convert("L")
 except Exception as e: raise GateError(f"editable mask unreadable: {e}") from e
 vals=set(mask.getdata())
 if mask.size!=base.size or not vals.issubset({0,255}) or 255 not in vals: raise GateError("editable mask must be binary, nonempty, and match baseline dimensions")
 d=ImageChops.difference(base,candidate)
 md=ImageChops.lighter(ImageChops.lighter(d.getchannel(0),d.getchannel(1)),d.getchannel(2))
 frozen=ImageChops.multiply(md,Image.eval(mask,lambda v:255 if v==0 else 0))
 if frozen.getbbox(): raise GateError("frozen-region pixel changes detected")
 g=m.get("geometry",{}); cam=g.get("base_camera_id")
 if not cam or cam!=g.get("adapted_module_camera_id"): raise GateError("base and adapted module camera IDs must match")
 fit=anchor_metrics(g.get("fit_anchors"),"fit_anchors",4); hold=anchor_metrics(g.get("holdout_anchors"),"holdout_anchors",2)
 fl,hl=float(g.get("fit_rms_limit_px",-1)),float(g.get("holdout_rms_limit_px",-1))
 if not math.isfinite(fl) or fl<0 or fit["rms_px"]>fl: raise GateError("fit anchor RMS exceeds limit")
 if not math.isfinite(hl) or hl<0 or hold["rms_px"]>hl: raise GateError("held-out anchor RMS exceeds limit")
 el,gl=float(g.get("max_edge_error_px",-1)),float(g.get("max_connection_gap_px",-1))
 for k,lim in (("platform_edge_max_error_px",el),("wall_joint_max_error_px",el),("stair_top_gap_px",gl),("stair_bottom_gap_px",gl)):
  v=float(g.get(k,-1))
  if not math.isfinite(lim) or lim<0 or not math.isfinite(v) or v<0 or v>lim: raise GateError(f"{k} fails threshold")
 clear,minimum=float(g.get("upper_exit_clearance_px",-1)),float(g.get("minimum_upper_exit_clearance_px",-1))
 if not math.isfinite(clear) or not math.isfinite(minimum) or minimum<0 or clear<minimum: raise GateError("upper exit clearance fails threshold")
 checks=m.get("structure_checks",{}); failed=[k for k in STRUCTURE if checks.get(k) is not True]
 if failed: raise GateError("structure checks missing/failed: "+", ".join(failed))
 return {"schema_version":1,"status":"CANDIDATE_READY_FOR_HUMAN_REVIEW","task_id":m.get("task_id","unspecified"),"manifest_sha256":digest(mp),"input_sha256":hashes,"image_size":list(base.size),"frozen_region_changed_pixels":0,"geometry":{"target_camera_id":cam,"fit_anchors":fit,"holdout_anchors":hold},"structure_checks":{k:True for k in STRUCTURE},"release_allowed":False,"note":"Technical checks passed; human review of exact candidate is still required."}

def emit(r,p=None):
 s=json.dumps(r,ensure_ascii=False,indent=2)+"\n"
 if p: Path(p).parent.mkdir(parents=True,exist_ok=True); Path(p).write_text(s,encoding="utf-8")
 print(s,end="")

def main():
 ap=argparse.ArgumentParser(); sub=ap.add_subparsers(dest="cmd",required=True)
 for cmd in ("check","release"):
  p=sub.add_parser(cmd); p.add_argument("--manifest",required=True); p.add_argument("--report")
  if cmd=="release": p.add_argument("--approval",required=True); p.add_argument("--output",required=True)
 a=ap.parse_args()
 try:
  r=validate(a.manifest)
  if a.cmd=="release":
   apath=Path(a.approval).resolve()
   try: approval=json.loads(apath.read_text(encoding="utf-8"))
   except Exception as e: raise GateError(f"approval unreadable: {e}") from e
   if approval.get("schema_version")!=1 or approval.get("approved") is not True or approval.get("reviewer_type")!="human" or not str(approval.get("reviewer","")).strip(): raise GateError("explicit human approval missing")
   if approval.get("candidate_sha256","")!=r["input_sha256"]["candidate_image"]: raise GateError("approval does not match exact candidate hash")
   stamp=approval.get("reviewed_at")
   if not isinstance(stamp,str): raise GateError("approval timestamp missing")
   dt=datetime.fromisoformat(stamp.replace("Z","+00:00"))
   if dt.tzinfo is None: raise GateError("approval timestamp must include timezone")
   m=json.loads(Path(a.manifest).read_text()); out=Path(a.output).resolve()
   if out.exists(): raise GateError("refusing to overwrite release")
   out.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(Path(a.manifest).resolve().parent/m["inputs"]["candidate_image"]["path"],out)
   if digest(out)!=r["input_sha256"]["candidate_image"]: out.unlink(missing_ok=True); raise GateError("release hash mismatch; rolled back")
   with Image.open(out) as im: im.verify()
   r.update(status="RELEASED",release_allowed=True,released_path=str(out),released_sha256=digest(out),approval_sha256=digest(apath))
  emit(r,a.report); return 0
 except Exception as e:
  emit({"schema_version":1,"status":"BLOCKED","release_allowed":False,"errors":[str(e)]},getattr(a,"report",None)); return 2
if __name__=="__main__": sys.exit(main())
