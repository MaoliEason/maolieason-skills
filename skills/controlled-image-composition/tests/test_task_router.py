import json, sys, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from task_router import RouterError, route_manifest, resolve_route, load_registry

def sha(p):
 import hashlib
 return hashlib.sha256(p.read_bytes()).hexdigest()

class RouterTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.r=Path(self.t.name)
  for d in ("inputs","qa","work"): (self.r/d).mkdir()
  Image.new("RGBA",(24,20),(30,40,50,255)).save(self.r/"inputs/base.png")
  module=Image.new("RGBA",(24,20),(0,0,0,0)); ImageDraw.Draw(module).rectangle((5,5,15,15),fill=(255,120,0,255)); module.save(self.r/"inputs/module.png")
  mask=Image.new("L",(24,20),0); ImageDraw.Draw(mask).rectangle((5,5,15,15),fill=255); mask.save(self.r/"qa/mask.png")
  self.registry=ROOT/"adapters"/"registry.json"
 def tearDown(self): self.t.cleanup()
 def write_manifest(self,task="local_composite",op="composite"):
  files={"base_image":"inputs/base.png","module_image":"inputs/module.png","approved_mask":"qa/mask.png"}
  if op!="composite": files={"source_image":"inputs/base.png"}
  m={"schema_version":1,"task_id":"router-test","task_type":task,"operation":op,"inputs":{k:{"path":v,"sha256":sha(self.r/v)} for k,v in files.items()},"parameters":{},"output":"work/candidate.png","receipt":"work/run_receipt.json"}
  p=self.r/"manifest.json"; p.write_text(json.dumps(m)); return p
 def test_supported_route_executes_and_returns_receipt(self):
  result=route_manifest(self.write_manifest(),self.registry)
  self.assertEqual(result["status"],"CANDIDATE_CREATED"); self.assertEqual(result["adapter_id"],"raster.masked_composite")
 def test_unknown_operation_blocked(self):
  p=self.write_manifest(task="local_composite",op="generate")
  with self.assertRaisesRegex(RouterError,"no adapter registered"): route_manifest(p,self.registry)
 def test_unimplemented_3d_route_blocked_not_fallback(self):
  p=self.write_manifest(task="3d_reconstruction",op="camera_match")
  with self.assertRaisesRegex(RouterError,"capability unavailable"): route_manifest(p,self.registry)
 def test_generation_adapter_not_executable(self):
  p=self.write_manifest(task="new_image_generation",op="generate")
  with self.assertRaisesRegex(RouterError,"capability unavailable"): route_manifest(p,self.registry)
 def test_mismatched_task_and_operation_blocked(self):
  p=self.write_manifest(task="raster_transform",op="composite")
  with self.assertRaisesRegex(RouterError,"no adapter registered"): route_manifest(p,self.registry)
 def test_registry_declares_unsupported_capabilities(self):
  r=load_registry(self.registry); tasks={a["task_type"]:a["status"] for a in r["adapters"]}
  self.assertEqual(tasks["3d_reconstruction"],"not_implemented")
  self.assertEqual(tasks["orthographic_views"],"not_implemented")
if __name__=="__main__": unittest.main()
