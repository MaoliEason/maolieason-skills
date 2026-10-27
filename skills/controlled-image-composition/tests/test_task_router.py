import hashlib, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from task_router import RouteError, route_manifest

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class RouterTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
  for d in ("inputs","models"): (self.root/d).mkdir()
  for name in ("base.png","module.png","source.png","style.png","mask.png"): (self.root/"inputs"/name).write_bytes(("fixture-"+name).encode())
  (self.root/"models"/"module.obj").write_text("o shared-model")
 def tearDown(self): self.tmp.cleanup()
 def entry(self,p): return {"path":p,"sha256":sha(self.root/p)}
 def base(self,t,m,i,tools=("python",),c=None): return {"schema_version":1,"task_type":t,"method":m,"inputs":i,"tools_used":list(tools),"constraints":c or {}}
 def test_creation_routes_to_generation(self):
  self.assertEqual(route_manifest(self.base("create_from_scratch","image_generation",{},("image_gen",)),self.root)["status"],"ROUTE_APPROVED_NOT_EXECUTED")
 def test_strict_edit_blocks_generative_method(self):
  m=self.base("edit_existing_image","explicit_ai_edit",{"base_image":self.entry("inputs/base.png"),"approved_mask":self.entry("inputs/mask.png")},("image_gen",),{"exact_local_edit":True})
  with self.assertRaisesRegex(RouteError,"cannot use a generative"): route_manifest(m,self.root)
 def test_strict_edit_blocks_generative_tool(self):
  m=self.base("edit_existing_image","controlled_masked_composite",{"base_image":self.entry("inputs/base.png"),"approved_mask":self.entry("inputs/mask.png")},("image_gen","python"),{"exact_local_edit":True})
  with self.assertRaisesRegex(RouteError,"generative tool"): route_manifest(m,self.root)
 def test_transform_requires_locked_source(self):
  m=self.base("transform_existing_image","rotate",{"source_image":self.entry("inputs/source.png")})
  self.assertEqual(route_manifest(m,self.root)["method"],"rotate")
 def test_composition_requires_mask(self):
  m=self.base("compose_images","layer_composite",{"base_image":self.entry("inputs/base.png"),"source_module":self.entry("inputs/module.png")},c={"preserve_pixels_outside_mask":True})
  with self.assertRaisesRegex(RouteError,"approved_mask"): route_manifest(m,self.root)
 def test_composition_with_mask_routes(self):
  m=self.base("compose_images","controlled_masked_composite",{"base_image":self.entry("inputs/base.png"),"source_module":self.entry("inputs/module.png"),"approved_mask":self.entry("inputs/mask.png")},c={"preserve_pixels_outside_mask":True})
  self.assertTrue(route_manifest(m,self.root)["strict_preservation"])
 def test_stale_hash_blocks(self):
  e=self.entry("inputs/source.png"); e["sha256"]="0"*64
  with self.assertRaisesRegex(RouteError,"SHA-256 mismatch"): route_manifest(self.base("transform_existing_image","rotate",{"source_image":e}),self.root)
 def test_unknown_task_blocks(self):
  with self.assertRaisesRegex(RouteError,"unsupported task_type"): route_manifest({"schema_version":1,"task_type":"stairs_only"},self.root)
 def test_orthographic_views_share_model(self):
  model=self.entry("models/module.obj"); h=model["sha256"]
  m=self.base("derive_orthographic_views","orthographic_render_from_single_3d_model",{"source_module":self.entry("inputs/module.png"),"model_source":model}); m["model_sha256"]=h
  m["views"]={v:{"projection":"orthographic","model_sha256":h} for v in ("front","side","top")}
  self.assertEqual(route_manifest(m,self.root)["task_type"],"derive_orthographic_views")
  m["views"]["side"]["model_sha256"]="wrong"
  with self.assertRaisesRegex(RouteError,"same locked model hash"): route_manifest(m,self.root)
if __name__=="__main__": unittest.main()
