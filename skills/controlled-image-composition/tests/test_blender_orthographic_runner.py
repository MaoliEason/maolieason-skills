import hashlib,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from blender_orthographic_runner import AdapterError,validate
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class BlenderManifestTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.root=Path(self.t.name)
  (self.root/"in").mkdir(); (self.root/"out").mkdir()
  scene=self.root/"in/scene.blend"; scene.write_bytes(b"synthetic scene placeholder")
  self.m={"schema_version":1,"task_id":"test","task_type":"orthographic_views","operation":"render_front_side_top","inputs":{"scene":{"path":"in/scene.blend","sha256":sha(scene)}},"render":{"cameras":{"front":"Camera_Front","side":"Camera_Side","top":"Camera_Top"},"resolution":[512,512],"format":"PNG"},"outputs":{v:{"path":f"out/{v}.png"} for v in ("front","side","top")},"receipt":"out/receipt.json","blender_executable":"/nonexistent/blender"}
  self.p=self.root/"manifest.json"; self.save()
 def tearDown(self): self.t.cleanup()
 def save(self): self.p.write_text(json.dumps(self.m))
 def test_bad_hash_blocks(self):
  self.m["inputs"]["scene"]["sha256"]="0"*64; self.save()
  with self.assertRaisesRegex(AdapterError,"SHA-256 mismatch"): validate(self.p)
 def test_missing_camera_blocks(self):
  del self.m["render"]["cameras"]["top"]; self.save()
  with self.assertRaisesRegex(AdapterError,"camera names"): validate(self.p)
 def test_invalid_resolution_blocks(self):
  self.m["render"]["resolution"]=[32,512]; self.save()
  with self.assertRaisesRegex(AdapterError,"resolution"): validate(self.p)
 def test_duplicate_outputs_block(self):
  self.m["outputs"]["top"]["path"]="out/front.png"; self.save()
  with self.assertRaisesRegex(AdapterError,"distinct"): validate(self.p)
 def test_missing_blender_runtime_blocks(self):
  self.save()
  with self.assertRaisesRegex(AdapterError,"Blender executable not found"): validate(self.p)
 def test_wrong_task_type_blocks(self):
  self.m["task_type"]="image_generation"; self.save()
  with self.assertRaisesRegex(AdapterError,"invalid orthographic"): validate(self.p)
if __name__=="__main__": unittest.main()
