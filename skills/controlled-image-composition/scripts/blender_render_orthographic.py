# Invoked by Blender; all views are rendered from the same loaded .blend scene.
import argparse,hashlib,json,sys
from pathlib import Path
import bpy
VIEWS=("front","side","top")
def sha(p):
 h=hashlib.sha256()
 with Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""): h.update(b)
 return h.hexdigest()
def safe(root,raw):
 q=Path(raw)
 if q.is_absolute() or ".." in q.parts: raise RuntimeError("unsafe output path")
 p=(root/q).resolve()
 if not p.is_relative_to(root.resolve()): raise RuntimeError("output outside task root")
 return p
def main():
 av=sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
 ap=argparse.ArgumentParser(); ap.add_argument("--manifest",required=True); a=ap.parse_args(av)
 mp=Path(a.manifest).resolve(); root=mp.parent; m=json.loads(mp.read_text())
 scene=safe(root,m["inputs"]["scene"]["path"])
 if sha(scene)!=m["inputs"]["scene"]["sha256"]: raise RuntimeError("scene hash mismatch")
 sc=bpy.context.scene; sc.render.resolution_x,sc.render.resolution_y=m["render"]["resolution"]; sc.render.resolution_percentage=100; sc.render.image_settings.file_format="PNG"
 for v in VIEWS:
  name=m["render"]["cameras"][v]; cam=bpy.data.objects.get(name)
  if cam is None or cam.type!="CAMERA" or cam.data.type!="ORTHO": raise RuntimeError(v+" camera missing or not orthographic")
  sc.camera=cam; out=safe(root,m["outputs"][v]["path"]); out.parent.mkdir(parents=True,exist_ok=True)
  if out.exists(): raise RuntimeError("refusing to overwrite "+v)
  sc.render.filepath=str(out); bpy.ops.render.render(write_still=True)
  if not out.is_file(): raise RuntimeError(v+" render not created")
 print("ORTHOGRAPHIC_RENDER_OK")
if __name__=="__main__": main()
