import hashlib, json, sys, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from controlled_image_runner import RunnerError, run, verify

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
class RunnerTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory(); self.r=Path(self.t.name)
  for d in ("inputs","qa","work"): (self.r/d).mkdir()
  Image.new("RGBA",(40,30),(30,40,50,255)).save(self.r/"inputs/base.png")
  mod=Image.new("RGBA",(40,30),(0,0,0,0)); ImageDraw.Draw(mod).rectangle((10,8,25,22),fill=(255,120,0,255)); mod.save(self.r/"inputs/module.png")
  mask=Image.new("L",(40,30),0); ImageDraw.Draw(mask).rectangle((10,8,25,22),fill=255); mask.save(self.r/"qa/mask.png")
 def tearDown(self): self.t.cleanup()
 def manifest(self, op="composite"):
  files={"base_image":"inputs/base.png","module_image":"inputs/module.png","approved_mask":"qa/mask.png"}
  if op=="rotate": files={"source_image":"inputs/module.png"}
  m={"schema_version":1,"task_id":"test","task_type":("local_composite" if op=="composite" else "planar_alignment" if op=="perspective_warp" else "raster_transform"),"operation":op,"inputs":{k:{"path":v,"sha256":sha(self.r/v)} for k,v in files.items()},"parameters":{"angle_degrees":17,"expand":True,"resampling":"bicubic"},"output":"work/candidate.png","receipt":"work/run_receipt.json"}
  p=self.r/"task.json"; p.write_text(json.dumps(m)); return p
 def test_masked_composite_and_receipt(self):
  _,rp=run(self.manifest()); self.assertEqual(verify(rp)["status"],"RECEIPT_VERIFIED")
  b=Image.open(self.r/"inputs/base.png").convert("RGB"); o=Image.open(self.r/"work/candidate.png").convert("RGB"); m=Image.open(self.r/"qa/mask.png")
  for y in range(30):
   for x in range(40):
    if m.getpixel((x,y))==0: self.assertEqual(b.getpixel((x,y)),o.getpixel((x,y)))
 def test_rotate_operation(self): self.assertEqual(verify(run(self.manifest("rotate"))[1])["status"],"RECEIPT_VERIFIED")
 def test_generative_operation_rejected(self):
  with self.assertRaisesRegex(RunnerError,"not allow-listed"): run(self.manifest("image_gen"))
 def test_hash_mismatch_rejected(self):
  p=self.manifest(); m=json.loads(p.read_text()); m["inputs"]["base_image"]["sha256"]="0"*64; p.write_text(json.dumps(m))
  with self.assertRaisesRegex(RunnerError,"SHA-256 mismatch"): run(p)
 def test_mask_size_mismatch_rejected(self):
  Image.new("L",(39,30),255).save(self.r/"qa/mask.png"); p=self.manifest()
  with self.assertRaisesRegex(RunnerError,"identical dimensions"): run(p)
 def test_overwrite_rejected(self):
  p=self.manifest(); (self.r/"work/candidate.png").write_bytes(b"preserve")
  with self.assertRaisesRegex(RunnerError,"overwrite"): run(p)
 def test_tampered_output_detected(self):
  _,rp=run(self.manifest()); Image.new("RGB",(40,30)).save(self.r/"work/candidate.png")
  with self.assertRaisesRegex(RunnerError,"hash differs"): verify(rp)

 def test_crop(self):
  p=self.manifest("crop"); m=json.loads(p.read_text()); m["parameters"]={"box":[2,3,22,18]}; p.write_text(json.dumps(m))
  _,rp=run(p); self.assertEqual(verify(rp)["size"],[20,15])
 def test_resize(self):
  p=self.manifest("resize"); m=json.loads(p.read_text()); m["parameters"]={"size":[21,17],"resampling":"nearest"}; p.write_text(json.dumps(m))
  _,rp=run(p); self.assertEqual(verify(rp)["size"],[21,17])
 def test_flip(self):
  p=self.manifest("flip"); m=json.loads(p.read_text()); m["parameters"]={"direction":"horizontal"}; p.write_text(json.dumps(m))
  _,rp=run(p); self.assertEqual(verify(rp)["status"],"RECEIPT_VERIFIED")
 def test_perspective_warp(self):
  p=self.manifest("perspective_warp"); m=json.loads(p.read_text()); m["parameters"]={"output_size":[40,30],"coefficients":[1,0,0,0,1,0,0,0],"resampling":"nearest"}; p.write_text(json.dumps(m))
  _,rp=run(p); self.assertEqual(verify(rp)["size"],[40,30])
 def test_wrong_task_type_blocked(self):
  p=self.manifest("crop"); m=json.loads(p.read_text()); m["task_type"]="local_composite"; p.write_text(json.dumps(m))
  with self.assertRaisesRegex(RunnerError,"task_type must"): run(p)
 def test_invalid_crop_blocked(self):
  p=self.manifest("crop"); m=json.loads(p.read_text()); m["parameters"]={"box":[-1,0,20,20]}; p.write_text(json.dumps(m))
  with self.assertRaisesRegex(RunnerError,"outside"): run(p)

if __name__=="__main__": unittest.main()
