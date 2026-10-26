import hashlib, sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from execution_guard import GuardError, validate_execution_contract

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

class ExecutionGuardTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
  for d in ("inputs","model","views"): (self.root/d).mkdir()
  (self.root/"inputs/source.png").write_bytes(b"approved source")
  (self.root/"model/module.obj").write_text("o module")
  for v in ("front","side","top"): (self.root/f"views/{v}.png").write_bytes(("view-"+v).encode())
  mh=sha(self.root/"model/module.obj"); sh=sha(self.root/"inputs/source.png")
  self.m={"inputs":{"source_module":{"path":"inputs/source.png","sha256":sh}},
   "execution":{"task_type":"orthographic_views_from_existing_module","method":"orthographic_render_from_single_3d_model","tools_used":["openscad","python"],"source_module_sha256":sh,"model_source":{"path":"model/module.obj","sha256":mh},"model_sha256":mh,
   "views":{v:{"path":f"views/{v}.png","sha256":sha(self.root/f"views/{v}.png"),"model_sha256":mh,"projection":"orthographic"} for v in ("front","side","top")}}}
 def tearDown(self): self.tmp.cleanup()
 def run_guard(self): return validate_execution_contract(self.m,self.root,self.m["inputs"]["source_module"]["sha256"])
 def test_same_model_orthographic_views_pass(self): self.assertEqual(self.run_guard()["method"],"orthographic_render_from_single_3d_model")
 def test_whole_image_generation_blocked(self):
  self.m["execution"]["tools_used"]=["image_gen"]
  with self.assertRaisesRegex(GuardError,"forbidden generative"): self.run_guard()
 def test_wrong_method_blocked(self):
  self.m["execution"]["method"]="prompt_only"
  with self.assertRaisesRegex(GuardError,"one shared 3D model"): self.run_guard()
 def test_different_model_hash_blocked(self):
  self.m["execution"]["views"]["side"]["model_sha256"]="other"
  with self.assertRaisesRegex(GuardError,"same model hash"): self.run_guard()
 def test_perspective_projection_blocked(self):
  self.m["execution"]["views"]["top"]["projection"]="perspective"
  with self.assertRaisesRegex(GuardError,"orthographic"): self.run_guard()
 def test_wrong_source_hash_blocked(self):
  self.m["execution"]["source_module_sha256"]="0"*64
  with self.assertRaisesRegex(GuardError,"source-module hash"): self.run_guard()
 def test_missing_view_blocked(self):
  del self.m["execution"]["views"]["top"]
  with self.assertRaisesRegex(GuardError,"front, side, and top"): self.run_guard()
 def test_wrong_model_hash_blocked(self):
  self.m["execution"]["model_sha256"]="0"*64
  with self.assertRaisesRegex(GuardError,"model source"): self.run_guard()
if __name__=="__main__": unittest.main()
