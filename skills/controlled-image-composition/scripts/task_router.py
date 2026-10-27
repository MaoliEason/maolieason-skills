#!/usr/bin/env python3
"""Generic image-work routing preflight; routes tasks but does not create images."""
import argparse, hashlib, json, sys
from pathlib import Path

ROUTES = {
 "create_from_scratch": ({"image_generation"}, set()),
 "edit_existing_image": ({"deterministic_2d_edit","controlled_masked_composite","3d_model_render_and_composite","explicit_ai_edit"}, {"base_image"}),
 "transform_existing_image": ({"rotate","crop","resize","perspective_transform","color_adjust"}, {"source_image"}),
 "compose_images": ({"controlled_masked_composite","layer_composite","3d_model_render_and_composite"}, {"base_image","source_module"}),
 "derive_orthographic_views": ({"orthographic_render_from_single_3d_model"}, {"source_module","model_source"}),
 "restore_image": ({"deterministic_restoration","explicit_ai_restoration"}, {"source_image"}),
 "style_transfer": ({"explicit_style_transfer"}, {"source_image","style_reference"}),
 "analyze_image": ({"visual_analysis"}, {"source_image"}),
 "layout_design": ({"layer_composite","design_generation"}, set()),
}
GENERATIVE = {"image_generation","explicit_ai_edit","explicit_ai_restoration","explicit_style_transfer","design_generation"}
FORBIDDEN = ("image_gen","text-to-image","whole-image-generation","generative-redraw","dall-e")
class RouteError(Exception): pass

def sha256(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()

def lock(root,item,label):
 if not isinstance(item,dict) or not isinstance(item.get("path"),str) or not item.get("sha256"): raise RouteError(f"{label}: locked relative path and SHA-256 required")
 raw=item["path"]
 if Path(raw).is_absolute() or ".." in Path(raw).parts: raise RouteError(f"{label}: unsafe relative path")
 p=(root/raw).resolve()
 if not p.is_relative_to(root.resolve()) or not p.is_file(): raise RouteError(f"{label}: file missing or outside task directory")
 actual=sha256(p)
 if actual != item["sha256"]: raise RouteError(f"{label}: SHA-256 mismatch")
 return {"path":raw,"sha256":actual}

def route_manifest(m,root):
 if m.get("schema_version")!=1: raise RouteError("schema_version must be 1")
 task,method=m.get("task_type"),m.get("method")
 if task not in ROUTES: raise RouteError(f"unsupported task_type: {task!r}")
 methods,required=ROUTES[task]
 if method not in methods: raise RouteError(f"method {method!r} is not allowed for task_type {task!r}")
 tools=m.get("tools_used")
 if not isinstance(tools,list) or not tools: raise RouteError("tools_used must list actual intended execution tools")
 tools=sorted({str(x).strip().lower() for x in tools})
 c=m.get("constraints",{})
 strict=bool(c.get("exact_local_edit") or c.get("preserve_geometry") or c.get("preserve_pixels_outside_mask"))
 if strict and method in GENERATIVE: raise RouteError("strict-preservation task cannot use a generative method")
 if strict and any(mark in tool for tool in tools for mark in FORBIDDEN): raise RouteError("generative tool declared for a strict-preservation task")
 inputs=m.get("inputs",{})
 needed=set(required)
 if task=="edit_existing_image" and c.get("exact_local_edit"): needed.add("approved_mask")
 if c.get("preserve_pixels_outside_mask"): needed.add("approved_mask")
 locked={key:lock(root,inputs.get(key),"inputs."+key) for key in sorted(needed)}
 if task=="compose_images" and not c.get("preserve_pixels_outside_mask"): raise RouteError("compose_images requires preserve_pixels_outside_mask=true and an approved mask")
 if task=="derive_orthographic_views":
  mh=locked["model_source"]["sha256"]
  if m.get("model_sha256")!=mh: raise RouteError("model_sha256 does not match locked model source")
  views=m.get("views")
  if not isinstance(views,dict) or any(v not in views for v in ("front","side","top")): raise RouteError("front, side, and top view definitions are required")
  for name in ("front","side","top"):
   if views[name].get("projection")!="orthographic" or views[name].get("model_sha256")!=mh: raise RouteError(f"{name} must use orthographic projection and the same locked model hash")
 return {"status":"ROUTE_APPROVED_NOT_EXECUTED","task_type":task,"method":method,"strict_preservation":strict,"locked_inputs":locked,"tools_used":tools,"next_step":"Run the method-specific adapter and verify its output. Routing is not production or acceptance."}

def main():
 p=argparse.ArgumentParser(); p.add_argument("--manifest",required=True); a=p.parse_args()
 try:
  mp=Path(a.manifest).resolve(); m=json.loads(mp.read_text(encoding="utf-8"))
  print(json.dumps(route_manifest(m,mp.parent),ensure_ascii=False,indent=2)); return 0
 except Exception as e:
  print(json.dumps({"status":"BLOCKED","error":str(e)},ensure_ascii=False,indent=2),file=sys.stderr); return 2
if __name__=="__main__": sys.exit(main())
